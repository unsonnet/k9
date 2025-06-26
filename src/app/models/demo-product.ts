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
];
