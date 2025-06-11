export type Query = {
  type: string;
  material: string;
  length: number | null;
  width: number | null;
  thickness: number | null;
  images: File[];
};

export type Reference = {
  type: string;
  material: string;
  length: number | null;
  width: number | null;
  thickness: number | null;
  images: string[];
};
