export type Query = {
      type: string;
      material: string;
      length: number | null;
      width: number | null;
      images: File[];
    }