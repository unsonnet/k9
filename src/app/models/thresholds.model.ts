import { FilterGroups } from './filter.model';

export type Thresholds = {
  [category: string]: {
    [metric: string]: [number, number];
  } & {
    missing: boolean;
  };
};

export function packageFilters(filters: FilterGroups): Thresholds {
  const result: Thresholds = {material : {material: [0, 0], missing: false}} as unknown as Thresholds;

  filters.forEach((group, category) => {
    const thresholds: { [metric: string]: [number, number] } = {};

    group.filters.forEach((filter, metric) => {
      thresholds[metric] = [0, category !== 'shape' ? 100 - filter.value : filter.value];
    });

    result[category] = {
      ...thresholds,
      missing: group.includeMissing,
    } as { [metric: string]: [number, number] } & { missing: boolean };
  });

  return result;
}
