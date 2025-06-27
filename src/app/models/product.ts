export type MetricSection = {
  [metric: string]: number;
};

export type Metrics = {
  product: {
    shape: MetricSection;
    color: MetricSection;
    pattern: MetricSection;
  };
  image: {
    color: MetricSection;
    pattern: MetricSection;
    variation: MetricSection;
  };
};

export type Product = {
  id: string;
  name: string;
  match: number;
  images: string[];
  scores: Metrics;
  description: {
    store: string;
    url: string;
    material: string;
    shape: {
      length?: number;
      width?: number;
      thickness?: number;
    };
  };
  starred?: boolean;
};
