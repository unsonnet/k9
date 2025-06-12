export type Reference<T extends File | string> = {
  type: string;
  material: string;
  length: number | null;
  width: number | null;
  thickness: number | null;
  images: T[];
};
