export type Filter = {
  label: string;
  type: string;
  value: number;
};

export type FilterGroups = Map<
  string,
  {
    label: string;
    filters: Map<string, Filter>;
    includeMissing: boolean;
  }
>;

export const shapeFilters = new Map([
  [
    'length',
    {
      label: 'Δ Length (in)',
      type: 'number',
      value: 1.5,
    },
  ],
  [
    'width',
    {
      label: 'Δ Width (in)',
      type: 'number',
      value: 1.5,
    },
  ],
]);

export const patternFilters = new Map([
  [
    'cosine',
    {
      label: 'Cosine',
      type: 'slider',
      value: 50,
    },
  ],
]);

export const colorFilters = new Map([
  [
    'chamfer',
    {
      label: 'Chamfer',
      type: 'slider',
      value: 50,
    },
  ],
  [
    'hausdorff',
    {
      label: 'Hausdorff',
      type: 'slider',
      value: 50,
    },
  ],
  [
    'variation',
    {
      label: 'Variation',
      type: 'slider',
      value: 50,
    },
  ],
  [
    'wasserstein',
    {
      label: 'Wasserstein',
      type: 'slider',
      value: 50,
    },
  ],
]);

export const filterGroups: FilterGroups = new Map([
  [
    'shape',
    {
      label: 'Shape',
      filters: shapeFilters,
      includeMissing: false,
    },
  ],
  [
    'pattern',
    {
      label: 'Pattern',
      filters: patternFilters,
      includeMissing: false,
    },
  ],
  [
    'color',
    {
      label: 'Color',
      filters: colorFilters,
      includeMissing: false,
    },
  ],
]);
