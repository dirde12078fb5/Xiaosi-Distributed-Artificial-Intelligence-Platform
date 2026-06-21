/* ==========================================================
   ConfigGUI · 节点库数据
   基于 ComfyUI 内置节点设计，参考：https://docs.comfy.org/zh/built-in-nodes/
   定义常见节点：模型加载 / 文本编码 / 采样 / 解码 / 图像处理等
   ========================================================== */

// 端口颜色调色板（按数据类型区分）
const PORT_COLORS = {
  MODEL: '#7aa2f7',      // 模型
  CLIP: '#bb9af7',       // CLIP 文本编码器
  VAE: '#9ece6a',        // VAE
  LATENT: '#e0af68',     // 潜空间
  IMAGE: '#7dcfff',      // 图像
  CONDITIONING: '#f7768e', // 条件
  MASK: '#73daca',       // 遮罩
  STRING: '#c0caf5',     // 字符串
  INT: '#ffd166',        // 整数
  FLOAT: '#ffb86c',      // 浮点
  BOOLEAN: '#c792ea',    // 布尔
  SEED: '#ff9e64',       // 种子
};

// 节点分类与节点定义
const NODE_LIBRARY = [
  {
    category: '加载器',
    color: PORT_COLORS.MODEL,
    nodes: [
      {
        type: 'CheckpointLoaderSimple',
        title: 'CheckpointLoaderSimple',
        description: '加载检查点模型（ckpt / safetensors），输出模型、CLIP 和 VAE。',
        inputs: [
          { name: 'ckpt_name', type: 'STRING', default: 'v1-5-pruned-emaonly.safetensors', control: 'text', label: '模型名称' },
        ],
        outputs: [
          { name: 'MODEL', type: 'MODEL' },
          { name: 'CLIP', type: 'CLIP' },
          { name: 'VAE', type: 'VAE' },
        ],
        params: [],
      },
      {
        type: 'VAELoader',
        title: 'VAELoader',
        description: '单独加载 VAE 模型。',
        inputs: [
          { name: 'vae_name', type: 'STRING', default: 'vae-ft-mse-840000.safetensors', control: 'text', label: 'VAE 名称' },
        ],
        outputs: [{ name: 'VAE', type: 'VAE' }],
      },
    ],
  },
  {
    category: '条件',
    color: PORT_COLORS.CONDITIONING,
    nodes: [
      {
        type: 'CLIPTextEncode',
        title: 'CLIPTextEncode',
        description: '使用 CLIP 将文本编码为条件向量，用于正向或反向提示。',
        inputs: [
          { name: 'clip', type: 'CLIP' },
          { name: 'text', type: 'STRING', default: 'masterpiece, best quality, 1girl, blue sky, cherry blossoms', control: 'textarea', label: '文本' },
        ],
        outputs: [{ name: 'COND', type: 'CONDITIONING' }],
      },
      {
        type: 'ConditioningZeroOut',
        title: 'ConditioningZeroOut',
        description: '将条件向量置零，提供一个中性起点。',
        inputs: [{ name: 'conditioning', type: 'CONDITIONING' }],
        outputs: [{ name: 'COND', type: 'CONDITIONING' }],
      },
    ],
  },
  {
    category: '采样',
    color: PORT_COLORS.LATENT,
    nodes: [
      {
        type: 'KSampler',
        title: 'KSampler',
        description: '核心扩散采样器，从模型采样出潜在图像。',
        inputs: [
          { name: 'model', type: 'MODEL' },
          { name: 'positive', type: 'CONDITIONING' },
          { name: 'negative', type: 'CONDITIONING' },
          { name: 'latent_image', type: 'LATENT' },
        ],
        outputs: [{ name: 'LATENT', type: 'LATENT' }],
        params: [
          { name: 'seed', type: 'INT', default: 1337, control: 'number', label: '种子 (seed)', min: 0, max: 9999999999 },
          { name: 'steps', type: 'INT', default: 20, control: 'number', label: '步数', min: 1, max: 100 },
          { name: 'cfg', type: 'FLOAT', default: 7.0, control: 'number', label: 'CFG', step: 0.1, min: 0, max: 30 },
          {
            name: 'sampler_name', type: 'STRING', default: 'euler', control: 'select', label: '采样器',
            options: ['euler', 'euler_ancestral', 'dpmpp_2m', 'dpmpp_sde', 'heun', 'dpm_2', 'dpm_2_ancestral', 'lms'],
          },
          {
            name: 'scheduler', type: 'STRING', default: 'normal', control: 'select', label: '调度器',
            options: ['normal', 'karras', 'simple', 'ddim_uniform'],
          },
          {
            name: 'denoise', type: 'FLOAT', default: 1.0, control: 'number', label: '去噪强度',
            step: 0.01, min: 0, max: 1,
          },
        ],
      },
      {
        type: 'KSamplerAdvanced',
        title: 'KSamplerAdvanced',
        description: '进阶采样器，可指定起始/结束步。',
        inputs: [
          { name: 'model', type: 'MODEL' },
          { name: 'positive', type: 'CONDITIONING' },
          { name: 'negative', type: 'CONDITIONING' },
          { name: 'latent_image', type: 'LATENT' },
        ],
        outputs: [{ name: 'LATENT', type: 'LATENT' }],
        params: [
          { name: 'seed', type: 'INT', default: 1337, control: 'number', label: '种子', min: 0 },
          { name: 'steps', type: 'INT', default: 20, control: 'number', label: '步数', min: 1 },
          { name: 'cfg', type: 'FLOAT', default: 7.0, control: 'number', label: 'CFG', step: 0.1 },
          { name: 'start_at_step', type: 'INT', default: 0, control: 'number', label: '起始步', min: 0 },
          { name: 'end_at_step', type: 'INT', default: 20, control: 'number', label: '结束步', min: 0 },
          { name: 'denoise', type: 'FLOAT', default: 1.0, control: 'number', label: '去噪强度', step: 0.01, min: 0, max: 1 },
        ],
      },
    ],
  },
  {
    category: '潜空间',
    color: PORT_COLORS.LATENT,
    nodes: [
      {
        type: 'EmptyLatentImage',
        title: 'EmptyLatentImage',
        description: '生成指定尺寸的空白潜在图像。',
        inputs: [],
        outputs: [{ name: 'LATENT', type: 'LATENT' }],
        params: [
          { name: 'width', type: 'INT', default: 512, control: 'number', label: '宽度', min: 64, max: 4096, step: 8 },
          { name: 'height', type: 'INT', default: 512, control: 'number', label: '高度', min: 64, max: 4096, step: 8 },
          { name: 'batch_size', type: 'INT', default: 1, control: 'number', label: '批次大小', min: 1, max: 64 },
        ],
      },
      {
        type: 'LatentUpscaleBy',
        title: 'LatentUpscaleBy',
        description: '按倍率放大潜在图像。',
        inputs: [{ name: 'samples', type: 'LATENT' }],
        outputs: [{ name: 'LATENT', type: 'LATENT' }],
        params: [
          {
            name: 'upscaler', type: 'STRING', default: 'nearest-exact', control: 'select', label: '上采样方法',
            options: ['nearest-exact', 'bilinear', 'area', 'bicubic'],
          },
          { name: 'scale_by', type: 'FLOAT', default: 1.5, control: 'number', label: '倍率', step: 0.1, min: 0.1 },
        ],
      },
    ],
  },
  {
    category: '解码',
    color: PORT_COLORS.VAE,
    nodes: [
      {
        type: 'VAEDecode',
        title: 'VAEDecode',
        description: '使用 VAE 将潜在图像解码为像素图像。',
        inputs: [
          { name: 'samples', type: 'LATENT' },
          { name: 'vae', type: 'VAE' },
        ],
        outputs: [{ name: 'IMAGE', type: 'IMAGE' }],
      },
      {
        type: 'VAEEncode',
        title: 'VAEEncode',
        description: '使用 VAE 将图像编码为潜在图像。',
        inputs: [
          { name: 'pixels', type: 'IMAGE' },
          { name: 'vae', type: 'VAE' },
        ],
        outputs: [{ name: 'LATENT', type: 'LATENT' }],
      },
    ],
  },
  {
    category: '图像',
    color: PORT_COLORS.IMAGE,
    nodes: [
      {
        type: 'LoadImage',
        title: 'LoadImage',
        description: '从文件加载图像。',
        inputs: [],
        outputs: [{ name: 'IMAGE', type: 'IMAGE' }, { name: 'MASK', type: 'MASK' }],
        params: [
          { name: 'image', type: 'STRING', default: 'example.png', control: 'text', label: '图像文件名' },
        ],
      },
      {
        type: 'SaveImage',
        title: 'SaveImage',
        description: '将图像保存到输出目录。',
        inputs: [{ name: 'images', type: 'IMAGE' }],
        outputs: [],
        params: [
          { name: 'filename_prefix', type: 'STRING', default: 'ComfyUI', control: 'text', label: '文件名前缀' },
        ],
      },
      {
        type: 'ImageScale',
        title: 'ImageScale',
        description: '缩放图像到指定尺寸。',
        inputs: [{ name: 'image', type: 'IMAGE' }],
        outputs: [{ name: 'IMAGE', type: 'IMAGE' }],
        params: [
          {
            name: 'method', type: 'STRING', default: 'lanczos', control: 'select', label: '插值方法',
            options: ['nearest-exact', 'bilinear', 'bicubic', 'lanczos'],
          },
          { name: 'width', type: 'INT', default: 512, control: 'number', label: '宽度', min: 1 },
          { name: 'height', type: 'INT', default: 512, control: 'number', label: '高度', min: 1 },
        ],
      },
      {
        type: 'ImageInvert',
        title: 'ImageInvert',
        description: '反转图像颜色。',
        inputs: [{ name: 'image', type: 'IMAGE' }],
        outputs: [{ name: 'IMAGE', type: 'IMAGE' }],
      },
    ],
  },
  {
    category: '高级',
    color: PORT_COLORS.PURPLE || '#bb9af7',
    nodes: [
      {
        type: 'SetNoise',
        title: 'SetNoiseSeed',
        description: '为工作流设置固定噪声种子，便于复现。',
        inputs: [{ name: 'noise', type: 'LATENT' }],
        outputs: [{ name: 'NOISE', type: 'LATENT' }],
        params: [
          { name: 'seed', type: 'INT', default: 0, control: 'number', label: '种子', min: 0 },
        ],
      },
      {
        type: 'Note',
        title: '备注 / Note',
        description: '一个纯文本备注，用于工作流文档化。',
        inputs: [],
        outputs: [],
        params: [
          { name: 'content', type: 'STRING', default: '在此记录本节点段的用途、参考或参数...', control: 'textarea', label: '内容' },
        ],
      },
    ],
  },
];

// 方便查找节点定义
function findNodeDefinition(type) {
  for (const group of NODE_LIBRARY) {
    for (const n of group.nodes) {
      if (n.type === type) return { def: n, color: group.color };
    }
  }
  return null;
}

// 暴露到全局
window.NODE_LIBRARY = NODE_LIBRARY;
window.PORT_COLORS = PORT_COLORS;
window.findNodeDefinition = findNodeDefinition;
