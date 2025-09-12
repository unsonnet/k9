export type MetricSection = {
  [metric: string]: number;
};

export type Metrics = {
  shape: MetricSection;
  color: MetricSection;
  pattern: MetricSection;
};

export type Product = {
  id: string;
  match: number;
  images: string[];
  scores: Metrics;
  description: {
    store: string;
    name: string;
    url: string;
    material: string;
    length?: number;
    width?: number;
    thickness?: number;
  };
  starred?: boolean;
};
