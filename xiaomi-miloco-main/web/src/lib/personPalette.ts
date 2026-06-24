/**
 * 家人头像背景色——6 套淡彩色派系(柔和、低饱和度的高色相),
 * 配白色 IconPerson 填充。所有家庭成员头像统一走 PersonAvatar 组件。
 */

export const palette: { bg: string }[] = [
  { bg: "#F5A29A" }, // 珊瑚粉
  { bg: "#F7C68A" }, // 蜜橘
  { bg: "#F2D86A" }, // 柠檬黄
  { bg: "#A6D8A4" }, // 薄荷绿
  { bg: "#9BC9E5" }, // 浅天蓝
  { bg: "#C5A6E3" }, // 浅紫丁香
];

export function paletteFor(hue: number) {
  return palette[hue % palette.length];
}

export function firstChar(name: string): string {
  return [...name][0] ?? "?";
}
