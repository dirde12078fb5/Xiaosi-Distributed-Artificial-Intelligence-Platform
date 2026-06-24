/**
 * 让它认识 X：5 段流程
 *   1. select-source  — 选入口（家里摄像头拍 / 上传视频 / 上传几张图）
 *   2. uploading      — 调 /api/identity/persons/{id}/extract 抽 body+face 候选
 *   3. picking        — 候选 grid:**算法自动预选**(用户可修改)
 *   4. saving         — 调 /samples/batch 入库
 *   5. done           — 成功提示
 *
 * 预选规则:
 * - 视频(单段 / 家里摄像头录制):后端 select_topk 算 auto_selected,前端默认勾这些
 * - 图片(多张上传):全选;若 >5 张默认勾前 5 张(用户多上传时也只取最差异化的前几张)
 *
 * 后端已迁移到主 backend(prefix /api/identity),不再依赖独立的 register_server 进程。
 */

import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { PerceptionCamera, Person } from "@/lib/types";
import {
  extractCandidates,
  fetchTierACounts,
  saveSamplesBatch,
  type ExtractCandidate,
} from "@/api/register";
import { useEscClose } from "@/hooks/useEscClose";
import { toast } from "./Toast";
import { IconCheck, IconX } from "@/lib/icons";
import { MiotRecorder } from "./MiotRecorder";

interface Props {
  person: Person;
  cameras: PerceptionCamera[];
  onClose: () => void;
  onDone: () => void;
}

type Stage = "select-source" | "uploading" | "picking" | "saving" | "done";

const MIN_BODY = 3;
const MIN_FACE = 3;
// 每类样本入库硬上限(镜像后端 ``tier_a_max // 2`` = 5)。注册时按"5 − 库内已存"
// 约束可勾选数,从源头杜绝存超被后端静默丢弃;库内已存来自 fetchTierACounts。
const MAX_PER_TYPE = 5;

export function EnrollFlow({ person, cameras, onClose, onDone }: Props) {
  const { t } = useTranslation();
  const [stage, setStage] = useState<Stage>("select-source");
  const [progress, setProgress] = useState<string>("");
  const [bodies, setBodies] = useState<ExtractCandidate[]>([]);
  const [faces, setFaces] = useState<ExtractCandidate[]>([]);
  const [pickedBodies, setPickedBodies] = useState<Set<number>>(new Set());
  const [pickedFaces, setPickedFaces] = useState<Set<number>>(new Set());
  // 库内已存的 body / face 数。可勾选额度 = MAX_PER_TYPE − 已存。拉取失败兜底为 0
  // (当作全新登记),最坏情况由 handleSave 的 failed 兜底提示接住。
  const [existingBody, setExistingBody] = useState(0);
  const [existingFace, setExistingFace] = useState(0);
  // 已提交的 bodies/faces 长度的同步镜像,作 appendAndPick 的 base offset。用 ref
  // 而非读 state:多文件循环里 state 的闭包快照不随 setState 更新(第 2 张图会拿到
  // 旧长度),而 ref 在事件里同步自增,跨轮 / 跨文件都拿到真实累计长度。
  const bodiesLenRef = useRef(0);
  const facesLenRef = useRef(0);
  // saving / uploading 期间挡 ESC + scrim 关闭:async 中途关 dialog 后,
  // 成功 reload 时住户已退出莫名刷新,失败 toast 弹到无 dialog 上下文。
  const isBusy = stage === "uploading" || stage === "saving";
  useEscClose(!isBusy, onClose);

  const remainBody = Math.max(0, MAX_PER_TYPE - existingBody);
  const remainFace = Math.max(0, MAX_PER_TYPE - existingFace);

  // 关掉后下一次再开是新一轮
  useEffect(() => {
    setStage("select-source");
    setBodies([]);
    setFaces([]);
    bodiesLenRef.current = 0;
    facesLenRef.current = 0;
    setPickedBodies(new Set());
    setPickedFaces(new Set());
    setExistingBody(0);
    setExistingFace(0);
    // 拉一次库内已存样本数(会话内不变——保存即结束流程)。失败静默兜底 0。
    //
    // 前瞻预留(reviewer 留意):当前唯一入口"让它认识X"门控在 !faceEnrolled 上,
    // 而有任意 tier_a 样本即 faceEnrolled=true,故今天能进到这里的人 existing 恒为
    // 0,下面这套"5 − 已存"额度逻辑等价于"固定上限 5"。之所以仍按已存计算、而非
    // 写死 5,是为将来可能引入的"给已认识的人追加/补充样本"入口预留——那条路径下
    // existing>0 才成真,届时本逻辑直接生效。详见 register.ts::fetchTierACounts。
    let cancelled = false;
    fetchTierACounts(person.id)
      .then((c) => {
        if (cancelled) return;
        setExistingBody(c.body);
        setExistingFace(c.face);
      })
      .catch(() => {
        /* 兜底当 0;saveSamplesBatch 的 failed 仍会接住存超 */
      });
    return () => {
      cancelled = true;
    };
  }, [person.id]);

  // 把一批新候选 append 到现有 bodies/faces,同时把对应的"应默认勾选"局部 indices
  // 翻译成全局 indices 加进 pickedBodies/pickedFaces。
  //
  // newCands 内的 type 决定它进哪个 group;defaultPickLocal 是相对 newCands 的局部
  // 下标 set。函数内部需要把局部下标转成"加进 group 之后的全局下标"。
  const appendAndPick = (
    newCands: ExtractCandidate[],
    defaultPickLocalIdx: Set<number>,
  ) => {
    // 先按出现顺序拆 body / face,记下"局部新候选 -> 该 group 内的新偏移"。
    const newBodies: ExtractCandidate[] = [];
    const newFaces: ExtractCandidate[] = [];
    const bodyPickLocal: number[] = []; // 在 newBodies 内的下标
    const facePickLocal: number[] = [];
    newCands.forEach((c, i) => {
      if (c.type === "body") {
        if (defaultPickLocalIdx.has(i)) bodyPickLocal.push(newBodies.length);
        newBodies.push(c);
      } else if (c.type === "face") {
        if (defaultPickLocalIdx.has(i)) facePickLocal.push(newFaces.length);
        newFaces.push(c);
      }
    });

    // base offset 取 ref(已提交长度的同步镜像),再各自更新——不在 setState updater
    // 内部嵌套调另一个 setState(那是 React 反模式,StrictMode 双调 updater 会让内层
    // 排两次)。自动预选累计不得超过本次可勾额度(MAX_PER_TYPE − 库内已存):多轮
    // "再传一段"各默认勾 5 会叠到 10,这里按 ns.size 截断,超出候选保留在 grid 但不勾。
    const baseBody = bodiesLenRef.current;
    const baseFace = facesLenRef.current;
    bodiesLenRef.current += newBodies.length;
    facesLenRef.current += newFaces.length;

    setBodies((prev) => [...prev, ...newBodies]);
    setPickedBodies((s) => {
      const ns = new Set(s);
      for (const li of bodyPickLocal) {
        if (ns.size >= remainBody) break;
        ns.add(baseBody + li);
      }
      return ns;
    });
    setFaces((prev) => [...prev, ...newFaces]);
    setPickedFaces((s) => {
      const ns = new Set(s);
      for (const li of facePickLocal) {
        if (ns.size >= remainFace) break;
        ns.add(baseFace + li);
      }
      return ns;
    });

    return { newBodies, newFaces };
  };

  const handleFiles = async (files: FileList | null, kind: "video" | "image") => {
    if (!files || files.length === 0) return;
    setStage("uploading");
    try {
      let totalBodies = 0;
      let totalFaces = 0;
      const arr = Array.from(files);
      for (let i = 0; i < arr.length; i++) {
        const f = arr[i];
        setProgress(t("family.analyzingProgress", { current: i + 1, total: arr.length }));
        const r = await extractCandidates(person.id, f, f.name);
        // 预选策略:
        // - 视频 / 多图视频路径走后端 auto_selected
        // - 图片路径(is_video=false):按 type 各自截到本次可勾额度(5 − 库内已存)
        const pickSet = computeDefaultPickSet(r, kind, remainBody, remainFace);
        const { newBodies, newFaces } = appendAndPick(r.candidates, pickSet);
        totalBodies += newBodies.length;
        totalFaces += newFaces.length;
      }
      if (totalBodies === 0 && totalFaces === 0) {
        toast(
          kind === "video"
            ? t("family.noPersonVideo")
            : t("family.noPersonImage"),
          "warn",
        );
        setStage("select-source");
        return;
      }
      setStage("picking");
    } catch (e) {
      const msg = e instanceof Error ? e.message : t("family.extractFail");
      toast(msg, "warn");
      setStage("select-source");
    }
  };

  const handleRecorded = async (blob: Blob) => {
    setStage("uploading");
    try {
      setProgress(t("family.analyzingVideo"));
      // 后端 record_clip 返回的是 BGR → libx264 重新编码出的 mp4;extract
      // 接 mp4 走 ffmpeg/decord 解码,跟 webm 路径一致。文件名后缀给 ffmpeg
      // 一点 probe 提示,实际解码靠内容。
      const filename = blob.type === "video/mp4" ? "recorded.mp4" : "recorded.webm";
      const r = await extractCandidates(person.id, blob, filename);
      const pickSet = computeDefaultPickSet(r, "video", remainBody, remainFace);
      const { newBodies, newFaces } = appendAndPick(r.candidates, pickSet);
      if (newBodies.length === 0 && newFaces.length === 0) {
        toast(t("family.noPersonRecord"), "warn");
        setStage("select-source");
        return;
      }
      setStage("picking");
    } catch (e) {
      const msg = e instanceof Error ? e.message : t("family.recordAnalyzeFail");
      toast(msg, "warn");
      setStage("select-source");
    }
  };

  const togglePick = (
    setter: (s: Set<number>) => void,
    set: Set<number>,
    i: number,
    label: string,
    existing: number,
  ) => {
    const next = new Set(set);
    if (next.has(i)) {
      next.delete(i);
      setter(next);
      return;
    }
    // 取消勾选随时可;新增勾选时卡"5 − 库内已存"额度,满了不加、弹提示。
    const cap = Math.max(0, MAX_PER_TYPE - existing);
    if (set.size >= cap) {
      toast(
        existing > 0
          ? t("family.capWithExisting", { label, max: MAX_PER_TYPE, existing, cap })
          : t("family.capPlain", { label, max: MAX_PER_TYPE }),
        "warn",
      );
      return;
    }
    next.add(i);
    setter(next);
  };

  const handleSave = async () => {
    // 达标看"库内已存 + 本次勾选"的总数:库内已够 MIN 的不强制本次再选。
    if (existingBody + pickedBodies.size < MIN_BODY) {
      toast(
        existingBody > 0
          ? t("family.minBodyWithExisting", { min: MIN_BODY, existing: existingBody })
          : t("family.minBody", { min: MIN_BODY }),
        "warn",
      );
      return;
    }
    if (existingFace + pickedFaces.size < MIN_FACE) {
      toast(
        existingFace > 0
          ? t("family.minFaceWithExisting", { min: MIN_FACE, existing: existingFace })
          : t("family.minFace", { min: MIN_FACE }),
        "warn",
      );
      return;
    }
    const items = [
      ...[...pickedBodies].map((i) => ({
        type: "body" as const,
        image_b64: bodies[i].image_b64,
      })),
      ...[...pickedFaces].map((i) => ({
        type: "face" as const,
        image_b64: faces[i].image_b64,
      })),
    ];
    // 库内已达标、本次没勾任何新样本:无需写盘(后端对空 items 返 400),直接完成。
    if (items.length === 0) {
      setStage("done");
      setTimeout(() => onDone(), 800);
      return;
    }
    setStage("saving");
    try {
      const res = await saveSamplesBatch(person.id, items);
      // 兜底防线:源头已按"5 − 已存"约束,正常不会再部分失败;但并发注册等
      // 竞态仍可能让后端写入失败,这里据 failed 明确告知,不再静默当全部成功。
      if (res.failed.length > 0) {
        toast(
          t("family.savePartialFail", {
            failed: res.failed.length,
            body: res.written_body,
            face: res.written_face,
          }),
          "warn",
        );
      }
      setStage("done");
      setTimeout(() => onDone(), 800);
    } catch (e) {
      const msg = e instanceof Error ? e.message : t("family.saveFailShort");
      toast(msg, "warn");
      setStage("picking");
    }
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4"
      onClick={isBusy ? undefined : onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="enroll-title"
        className="w-full max-w-3xl bg-bg-secondary rounded-xl border border-border shadow-sm p-6 anim-in max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3
            id="enroll-title"
            className="text-title text-text-primary"
          >
            {t("family.enrollTitle", { name: person.name })}
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1 text-text-secondary hover:text-text-primary"
            aria-label={t("family.close")}
          >
            <IconX />
          </button>
        </div>

        {stage === "select-source" && (
          <SourcePicker
            cameras={cameras}
            onPickFiles={handleFiles}
            onRecorded={handleRecorded}
          />
        )}

        {(stage === "uploading" || stage === "saving") && (
          <div className="py-12 text-center">
            <div className="text-title text-text-primary mb-2">
              {stage === "uploading"
                ? progress || t("family.analyzing")
                : t("family.savingState")}
            </div>
            <div className="text-caption text-text-secondary">
              {t("family.enrollLongVideoHint")}
            </div>
          </div>
        )}

        {stage === "picking" && (
          <CandidatePicker
            bodies={bodies}
            faces={faces}
            pickedBodies={pickedBodies}
            pickedFaces={pickedFaces}
            existingBody={existingBody}
            existingFace={existingFace}
            onToggleBody={(i) => togglePick(setPickedBodies, pickedBodies, i, t("family.labelBody"), existingBody)}
            onToggleFace={(i) => togglePick(setPickedFaces, pickedFaces, i, t("family.labelFace"), existingFace)}
            onAddMore={() => setStage("select-source")}
            onSave={handleSave}
          />
        )}

        {stage === "done" && (
          <div className="py-12 text-center">
            <div className="text-display text-success mb-2">✓</div>
            <div className="text-title text-text-primary">
              {t("family.enrollDone", { name: person.name })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// 视频路径:后端 auto_selected.body / .face 给的就是 candidates 数组的全局下标,
// 直接合并成 set 返回。
// 图片路径:不用后端预选,前端按 type 各自截到 capBody / capFace(本次可勾额度)作为默认勾选。
// 返回值是相对入参 r.candidates 的局部下标 set;appendAndPick 内部会再映射成全局下标。
function computeDefaultPickSet(
  r: { candidates: ExtractCandidate[]; auto_selected: { body: number[]; face: number[] } },
  kind: "video" | "image",
  capBody: number,
  capFace: number,
): Set<number> {
  const out = new Set<number>();
  if (kind === "video") {
    // 视频走后端 auto_selected;最终累计仍由 appendAndPick 按可勾额度截断。
    r.auto_selected.body.forEach((i) => out.add(i));
    r.auto_selected.face.forEach((i) => out.add(i));
    return out;
  }
  // image 路径:按 type 分别截到本次可勾额度(5 − 库内已存)。
  let bodyCnt = 0;
  let faceCnt = 0;
  r.candidates.forEach((c, i) => {
    if (c.type === "body" && bodyCnt < capBody) {
      out.add(i);
      bodyCnt += 1;
    } else if (c.type === "face" && faceCnt < capFace) {
      out.add(i);
      faceCnt += 1;
    }
  });
  return out;
}

// ── 入口选择 ────────────────────────────────────────────────
function SourcePicker({
  cameras,
  onPickFiles,
  onRecorded,
}: {
  cameras: PerceptionCamera[];
  onPickFiles: (files: FileList | null, kind: "video" | "image") => void;
  onRecorded: (blob: Blob) => void;
}) {
  const { t } = useTranslation();
  const [recording, setRecording] = useState(false);

  if (recording) {
    return (
      <MiotRecorder
        cameras={cameras}
        onCancel={() => setRecording(false)}
        onDone={(blob) => {
          setRecording(false);
          onRecorded(blob);
        }}
      />
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-caption text-text-secondary mb-2">
        {t("family.sourceHint")}
      </p>

      {cameras.length > 0 && (
        <SourceCard
          title={t("family.sourceCameraTitle")}
          hint={t("family.sourceCameraHint")}
        >
          <button
            type="button"
            onClick={() => setRecording(true)}
            className="inline-block px-4 py-2 rounded-lg bg-brand-primary text-white hover:bg-brand-accent"
          >
            {t("family.startRecord")}
          </button>
        </SourceCard>
      )}

      <SourceCard
        title={t("family.sourceVideoTitle")}
        hint={t("family.sourceVideoHint")}
      >
        <label className="cursor-pointer">
          <input
            type="file"
            accept="video/*"
            className="hidden"
            onChange={(e) => onPickFiles(e.target.files, "video")}
          />
          <span className="inline-block px-4 py-2 rounded-lg bg-bg-primary border border-border text-text-secondary hover:text-text-primary">
            {t("family.pickVideo")}
          </span>
        </label>
      </SourceCard>

      <SourceCard
        title={t("family.sourcePhotoTitle")}
        hint={t("family.sourcePhotoHint")}
      >
        <label className="cursor-pointer">
          <input
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={(e) => onPickFiles(e.target.files, "image")}
          />
          <span className="inline-block px-4 py-2 rounded-lg bg-bg-primary border border-border text-text-secondary hover:text-text-primary">
            {t("family.pickPhoto")}
          </span>
        </label>
      </SourceCard>
    </div>
  );
}

function SourceCard({
  title,
  hint,
  children,
}: {
  title: string;
  hint: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl bg-bg-primary border border-border p-4">
      <div className="text-title text-text-primary">{title}</div>
      <div className="text-caption text-text-secondary mt-1 mb-3">
        {hint}
      </div>
      {children}
    </div>
  );
}

// ── 候选挑选 ────────────────────────────────────────────────
function CandidatePicker({
  bodies,
  faces,
  pickedBodies,
  pickedFaces,
  existingBody,
  existingFace,
  onToggleBody,
  onToggleFace,
  onAddMore,
  onSave,
}: {
  bodies: ExtractCandidate[];
  faces: ExtractCandidate[];
  pickedBodies: Set<number>;
  pickedFaces: Set<number>;
  existingBody: number;
  existingFace: number;
  onToggleBody: (i: number) => void;
  onToggleFace: (i: number) => void;
  onAddMore: () => void;
  onSave: () => void;
}) {
  const { t } = useTranslation();
  // 达标 / 额度都按"库内已存 + 本次勾选"算。
  const okBody = existingBody + pickedBodies.size >= MIN_BODY;
  const okFace = existingFace + pickedFaces.size >= MIN_FACE;
  const remainBody = Math.max(0, MAX_PER_TYPE - existingBody);
  const remainFace = Math.max(0, MAX_PER_TYPE - existingFace);

  // 标题:库内有存 / 已满 / 全新 三种措辞。
  const groupTitle = (
    label: string, picked: number, total: number, existing: number, remain: number,
  ): string => {
    if (existing >= MAX_PER_TYPE) {
      return t("family.groupFull", { label, max: MAX_PER_TYPE });
    }
    if (existing > 0) {
      return t("family.groupWithExisting", { label, existing, picked, remain, total });
    }
    return t("family.groupFresh", { label, picked, remain, total });
  };

  return (
    <div>
      <p className="text-caption text-text-secondary mb-1">
        {t("family.pickerCapHint", { max: MAX_PER_TYPE, min: MIN_BODY })}
      </p>
      <p className="text-caption text-brand-primary mb-3">
        {t("family.pickerAutoHint")}
      </p>

      <CandidateGroup
        title={groupTitle(t("family.labelBody"), pickedBodies.size, bodies.length, existingBody, remainBody)}
        ok={okBody}
        candidates={bodies}
        picked={pickedBodies}
        onToggle={onToggleBody}
        variant="body"
      />
      <CandidateGroup
        title={groupTitle(t("family.labelFace"), pickedFaces.size, faces.length, existingFace, remainFace)}
        ok={okFace}
        candidates={faces}
        picked={pickedFaces}
        onToggle={onToggleFace}
        variant="face"
      />

      <div className="flex justify-between items-center mt-4 pt-3 border-t border-border">
        <button
          type="button"
          onClick={onAddMore}
          className="text-caption text-text-secondary hover:text-text-primary"
        >
          {t("family.addMore")}
        </button>
        <button
          type="button"
          onClick={onSave}
          disabled={!okBody || !okFace}
          className="px-5 py-2 rounded-lg bg-brand-primary text-white hover:bg-brand-accent disabled:opacity-60"
        >
          <IconCheck className="inline mr-1" />
          {t("family.save")}
        </button>
      </div>
    </div>
  );
}

function CandidateGroup({
  title,
  ok,
  candidates,
  picked,
  onToggle,
  variant,
}: {
  title: string;
  ok: boolean;
  candidates: ExtractCandidate[];
  picked: Set<number>;
  onToggle: (i: number) => void;
  variant: "body" | "face";
}) {
  const { t } = useTranslation();
  // body / face 长宽比有别:
  //  - body 是 detector 给的人体竖向 bbox,常见 1:2 左右,grid 用 aspect-[1/2]
  //    匹配, object-contain 缩放保原比例(不裁不拉),配合 bg-black 留边
  //    填空白处,避免之前 aspect-square + object-cover 把头 / 脚都裁掉。
  //  - face 偏方,1:1 仍然合适,但同样改 object-contain 防把头顶 / 下巴吃掉。
  const aspect = variant === "body" ? "aspect-[1/2]" : "aspect-square";
  return (
    <div className="mb-4">
      <div className={`text-caption mb-2 ${ok ? "text-success" : "text-text-secondary"}`}>
        {ok && "✓ "}
        {title}
      </div>
      {candidates.length === 0 ? (
        <div className="text-caption text-text-tertiary rounded-lg bg-bg-primary py-6 text-center">
          {t("family.noSamplesExtracted")}
        </div>
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
          {candidates.map((c, i) => {
            const on = picked.has(i);
            return (
              <button
                key={i}
                type="button"
                onClick={() => onToggle(i)}
                className={`relative rounded-lg overflow-hidden border-2 transition-colors ${aspect} bg-black ${
                  on
                    ? "border-brand-primary ring-2 ring-brand-ring"
                    : "border-border hover:border-border-strong"
                }`}
              >
                <img
                  src={`data:image/jpeg;base64,${c.image_b64}`}
                  alt=""
                  className="w-full h-full object-contain"
                />
                {on && (
                  <span className="absolute top-1 right-1 bg-brand-primary text-white rounded-full w-5 h-5 flex items-center justify-center text-caption">
                    ✓
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
