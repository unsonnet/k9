export type ThresholdSection = {
  [metric: string]: [number, number];
} & { missing: boolean };

export type Thresholds = {
  product: {
    material: ThresholdSection;
    shape: ThresholdSection;
    color: ThresholdSection;
    pattern: ThresholdSection;
  };
  image: {
    color: ThresholdSection;
    pattern: ThresholdSection;
    variation: ThresholdSection;
  };
};
