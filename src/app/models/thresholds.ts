export type ThresholdSection = {
  [metric: string]: number;
} & { missing: boolean };

export type Thresholds = {
  type_: ThresholdSection;
  shape: ThresholdSection;
  color: ThresholdSection;
  pattern: ThresholdSection;
};
