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
    id: 'p000',
    store: 'Happy Floors',
    name: 'Artisan & Artisan Wall Dark/Glossy',
    images: [
      'https://nativo-inc-k9.s3.amazonaws.com/catalog/album/012d81b9-fed8-43d9-8432-5c9471050a60.54573-9446-L.c2a4d5d7-7e95-4fd0-8dc8-88a6910101d8.png?...',
    ],
    scores: {
      pattern: {
        cosine: [[45.08927127056385]],
      },
      color: {
        chamfer: [[23.894516615746465]],
        hausdorff: [[29.876813368710543]],
        variation: [[34.99146239110931]],
        wasserstein: [[9.544337813541741]],
      },
    },
    details: {
      url: 'https://www.happy-floors.com/product/artisan-artisan-wall/#9446-L',
      material: 'porcelain',
      length: null,
      width: null,
      thickness: null,
    },
  },
  {
    id: 'p001',
    store: 'Happy Floors',
    name: 'Nextone Grey/Natural',
    images: [
      'https://nativo-inc-k9.s3.amazonaws.com/catalog/album/016abce5-879e-480b-ab62-6abb72b59ca6.46610-7389-L.2bdff57e-e92e-4ddb-aafe-a3d67e937028.png?...',
    ],
    scores: {
      pattern: {
        cosine: [[3.3165279072029152]],
      },
      color: {
        chamfer: [[17.714517016306967]],
        hausdorff: [[33.86207401380857]],
        variation: [[72.54684067709005]],
        wasserstein: [[10.87956898248683]],
      },
    },
    details: {
      url: 'https://www.happy-floors.com/product/nextone/#7389-L',
      material: 'porcelain',
      length: null,
      width: null,
      thickness: null,
    },
  },
];
