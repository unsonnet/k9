import type { Product } from './product';

export const exampleProducts: Product[] = [
  {
    id: 'prod001',
    match: 0,
    images: [
      'https://picsum.photos/id/1018/400/400',
      'https://picsum.photos/id/100/400/400',
    ],
    scores: {
      shape: { length: 8, width: 8, thickness: 2 },
      color: { red: 0.7, green: 0.2, blue: 0.1 },
      pattern: { striped: 0.5, dotted: 0.3 },
    },
    description: {
      store: 'Glasshouse',
      name: 'Sunset Glassware Set',
      url: 'https://example.com/prod001',
      material: 'ceramic',
      length: 8,
      width: 8,
      thickness: 2,
    },
  },
  {
    id: 'prod002',
    match: 1,
    images: ['https://picsum.photos/id/1027/400/400'],
    scores: {
        shape: { length: 6, width: 6, thickness: 3 },
        color: { red: 0.2, green: 0.3, blue: 0.6 },
        pattern: { dotted: 0.7 },
    },
    description: {
      store: 'Craftware Co.',
      name: 'Minimalist Ceramic Bowl',
      url: 'https://example.com/prod002',
      material: 'ceramic',
      length: 6,
      width: 6,
      thickness: 3,
    },
  },
  {
    id: 'prod003',
    match: 2,
    images: ['https://picsum.photos/id/1041/400/400'],
    scores: {
        shape: { length: 12, width: 7, thickness: 6 },
        color: { red: 0.4, green: 0.5, blue: 0.2 },
        pattern: { striped: 0.6 },
    },
    description: {
      store: 'BrewHouse',
      name: 'Modernist Teapot',
      url: 'https://example.com/prod003',
      material: 'ceramic',
      length: 12,
      width: 7,
      thickness: 6,
    },
  },
  {
    id: 'prod004',
    match: 3,
    images: [
      'https://picsum.photos/id/1062/400/400',
      'https://picsum.photos/id/1069/400/400',
    ],
    scores: {
        shape: { length: 10, width: 10, thickness: 1 },
        color: { red: 0.1, green: 0.4, blue: 0.8 },
        pattern: { dotted: 0.4, striped: 0.2 },
    },
    description: {
      store: 'BlueClay Studio',
      name: 'Azure Porcelain Plate',
      url: 'https://example.com/prod004',
      material: 'porcelain',
      length: 10,
      width: 10,
      thickness: 1,
    },
  },
  {
    id: 'prod005',
    match: 4,
    images: ['https://picsum.photos/id/1076/400/400'],
    scores: {
        shape: { length: 5, width: 5, thickness: 2 },
        color: { red: 0.5, green: 0.5, blue: 0.5 },
        pattern: { dotted: 0.9 },
    },
    description: {
      store: 'TinyPlates',
      name: 'Speckled Dessert Dish',
      url: 'https://example.com/prod005',
      material: 'stoneware',
      length: 5,
      width: 5,
      thickness: 2,
    },
  },
  {
    id: 'prod006',
    match: 5,
    images: ['https://picsum.photos/id/1084/400/400'],
    scores: {
        shape: { length: 9, width: 6, thickness: 4 },
        color: { red: 0.8, green: 0.3, blue: 0.1 },
        pattern: { striped: 0.3 },
    },
    description: {
      store: 'Glassroots',
      name: 'Amber Glass Mug',
      url: 'https://example.com/prod006',
      material: 'glass',
      length: 9,
      width: 6,
      thickness: 4,
    },
  },
];
