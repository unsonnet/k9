export type ThresholdSection = {
  [metric: string]: [number, number];
} & { missing: boolean };

export type Thresholds = {
  material: ThresholdSection;
  shape: ThresholdSection;
  color: ThresholdSection;
  pattern: ThresholdSection;
};
