import { Product } from '../models/product.model';
import { mockReference } from './reference.data';

const M = mockReference.length;

function generateSparseMatrix(rows: number, cols: number): (number | null)[][] {
  return Array.from({ length: rows }, () =>
    Array.from({ length: cols }, () =>
      Math.random() < 0.7 ? +Math.random().toFixed(2) : null,
    ),
  );
}

export const mockProducts: Product[] = [
  {
    id: 'p001',
    store: 'TechGear',
    name: 'Wireless Noise-Cancelling Over-Ear Headphones with Long Battery Life',
    images: [
      'https://placehold.co/150x100?text=Headphones',
      'https://placehold.co/200x200?text=Shirt',
      'https://placehold.co/150x150?text=Pants',
    ],
    scores: {
      quality: {
        sharpness: generateSparseMatrix(3, M),
        brightness: generateSparseMatrix(3, M),
      },
      aesthetics: {
        symmetry: generateSparseMatrix(3, M),
      },
    },
    details: {
      price: 299.99,
      brand: 'SoundPro',
      color: 'Black',
      weight: 320,
      warranty: '2 years',
    },
  },
  {
    id: 'p002',
    store: 'EcoStyle',
    name: 'Reusable Stainless Steel Water Bottle (750ml)',
    images: ['https://placehold.co/150x100?text=Bottle'],
    scores: {
      quality: {
        sharpness: generateSparseMatrix(1, M),
        brightness: generateSparseMatrix(1, M),
      },
      aesthetics: {
        symmetry: generateSparseMatrix(1, M),
      },
    },
    details: {
      price: 25.5,
      brand: 'HydroClean',
      color: 'Silver',
      weight: 500,
      warranty: null,
    },
  },
  {
    id: 'p003',
    store: 'HomeEssentials',
    name: 'Ergonomic Office Chair with Adjustable Height and Lumbar Support',
    images: ['https://placehold.co/150x100?text=Chair'],
    scores: {
      quality: {
        sharpness: generateSparseMatrix(1, M),
        brightness: generateSparseMatrix(1, M),
      },
      aesthetics: {
        symmetry: generateSparseMatrix(1, M),
      },
    },
    details: {
      price: 189.99,
      brand: 'SitWell',
      color: 'Gray',
      weight: 15000,
      warranty: '3 years',
    },
  },
];
