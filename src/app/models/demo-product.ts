import type { Product } from './product';

export const exampleProducts: Product[] = [
  {
    id: 'prod001',
    name: 'Sunset Glassware Set',
    images: [
      'https://picsum.photos/id/1018/400/400',
      'https://picsum.photos/id/100/400/400',
    ],
    scores: {
      product: {
        shape: { length: 8, width: 8, thickness: 2 },
        color: { red: 0.7, green: 0.2, blue: 0.1 },
        pattern: { striped: 0.5, dotted: 0.3 },
      },
      image: {
        color: { saturation: 0.8, brightness: 0.6 },
        pattern: { noise: 0.1 },
        variation: { angle: 15, scale: 1.1 },
      },
    },
    description: {
      store: 'Glasshouse',
      url: 'https://example.com/prod001',
      material: 'ceramic',
      shape: { length: 8, width: 8, thickness: 2 },
    },
  },
  {
    id: 'prod002',
    name: 'Minimalist Ceramic Bowl',
    images: ['https://picsum.photos/id/1027/400/400'],
    scores: {
      product: {
        shape: { length: 6, width: 6, thickness: 3 },
        color: { red: 0.2, green: 0.3, blue: 0.6 },
        pattern: { dotted: 0.7 },
      },
      image: {
        color: { saturation: 0.3, brightness: 0.7 },
        pattern: { noise: 0.2 },
        variation: { angle: 5, scale: 1.0 },
      },
    },
    description: {
      store: 'Craftware Co.',
      url: 'https://example.com/prod002',
      material: 'ceramic',
      shape: { length: 6, width: 6, thickness: 3 },
    },
  },
  {
    id: 'prod003',
    name: 'Modernist Teapot',
    images: ['https://picsum.photos/id/1041/400/400'],
    scores: {
      product: {
        shape: { length: 12, width: 7, thickness: 6 },
        color: { red: 0.4, green: 0.5, blue: 0.2 },
        pattern: { striped: 0.6 },
      },
      image: {
        color: { saturation: 0.6, brightness: 0.8 },
        pattern: { noise: 0.1 },
        variation: { angle: 10, scale: 1.05 },
      },
    },
    description: {
      store: 'BrewHouse',
      url: 'https://example.com/prod003',
      material: 'ceramic',
      shape: { length: 12, width: 7, thickness: 6 },
    },
  },
  {
    id: 'prod004',
    name: 'Azure Porcelain Plate',
    images: [
      'https://picsum.photos/id/1062/400/400',
      'https://picsum.photos/id/1069/400/400',
    ],
    scores: {
      product: {
        shape: { length: 10, width: 10, thickness: 1 },
        color: { red: 0.1, green: 0.4, blue: 0.8 },
        pattern: { dotted: 0.4, striped: 0.2 },
      },
      image: {
        color: { saturation: 0.5, brightness: 0.9 },
        pattern: { noise: 0.15 },
        variation: { angle: 20, scale: 0.95 },
      },
    },
    description: {
      store: 'BlueClay Studio',
      url: 'https://example.com/prod004',
      material: 'porcelain',
      shape: { length: 10, width: 10, thickness: 1 },
    },
  },
  {
    id: 'prod005',
    name: 'Speckled Dessert Dish',
    images: ['https://picsum.photos/id/1076/400/400'],
    scores: {
      product: {
        shape: { length: 5, width: 5, thickness: 2 },
        color: { red: 0.5, green: 0.5, blue: 0.5 },
        pattern: { dotted: 0.9 },
      },
      image: {
        color: { saturation: 0.2, brightness: 0.4 },
        pattern: { noise: 0.3 },
        variation: { angle: 0, scale: 1.0 },
      },
    },
    description: {
      store: 'TinyPlates',
      url: 'https://example.com/prod005',
      material: 'stoneware',
      shape: { length: 5, width: 5, thickness: 2 },
    },
  },
  {
    id: 'prod006',
    name: 'Amber Glass Mug',
    images: ['https://picsum.photos/id/1084/400/400'],
    scores: {
      product: {
        shape: { length: 9, width: 6, thickness: 4 },
        color: { red: 0.8, green: 0.3, blue: 0.1 },
        pattern: { striped: 0.3 },
      },
      image: {
        color: { saturation: 0.7, brightness: 0.5 },
        pattern: { noise: 0.05 },
        variation: { angle: 12, scale: 1.2 },
      },
    },
    description: {
      store: 'Glassroots',
      url: 'https://example.com/prod006',
      material: 'glass',
      shape: { length: 9, width: 6, thickness: 4 },
    },
  },
];
