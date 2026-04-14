export type Embedding = {
  vector: number[];
  similarity?: number; // Percent similarity when used in search results
};
export type MiniEmbedding = {
  vector: [number, number];
  similarity?: number; // Percent similarity when used in search results
};
export type Dimensional<T> = {
  val: number;
  unit: T;
};

export type ProductImage = {
  id: string;
  url: string;
  mask?: string;
  selection?: {
    shape: { width: number; height: number };
    position: { x: number; y: number };
    scale: number;
    rotation: { x: number; y: number; z: number; w: number };
  };
};

export type Product = {
  id: string;
  brand?: string;
  series?: string;
  model: string;
  images: ProductImage[];
  category: {
    type?: string;
    material?: string;
    look?: string;
    texture?: string;
    finish?: string;
    edge?: string;
  };
  formats: {
    length?: Dimensional<'none' | 'in'>;
    width?: Dimensional<'none' | 'in'>;
    thickness?: Dimensional<'mm'>;
    vendors: {
      sku: string;
      store: string;
      name: string;
      price?: Dimensional<'usd'>;
      discontinued?: boolean;
      url: string;
    }[];
  }[];
  analysis?: {
    color: { primary: Embedding; secondary: Embedding };
    pattern: { primary: Embedding; secondary: Embedding };
    similarity: number;
  };
};

export type ProductIndex = {
  id: string;
  brand: string;
  series?: string;
  model: string;
  image: string;
  match?: number;
  analysis?: {
    color: { primary: MiniEmbedding; secondary: MiniEmbedding };
    pattern: { primary: MiniEmbedding; secondary: MiniEmbedding };
    similarity: number;
  };
};

export type Report<T extends Product | ProductIndex = Product | ProductIndex> = {
  id: string;
  title: string;
  author: string;
  date: string; // ISO string
  reference: T;
  favorites?: string[]; // Array of favorited ProductIndex IDs for this report
};

// A dashboard-friendly report where the reference is a single ProductImage used for previews
export type ReportPreview = Omit<Report<Product | ProductIndex>, 'reference'> & {
  reference: ProductImage;
};
