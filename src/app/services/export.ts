import { Injectable } from '@angular/core';
import JSZip from 'jszip';
import { Product } from '../models/product';
import { Reference } from '../models/reference';

@Injectable({
  providedIn: 'root',
})
export class Export {
  constructor() {}

  async exportProducts(reference: Reference<string>, products: Product[]) {
    const zip = new JSZip();
    const csvRows = ['id,name,store,url,material,length,width,thickness'];

    // --- Reference entry ---
    csvRows.push(
      [
        0,
        '"REFERENCE"',
        '',
        '',
        `"${reference.material}"`,
        reference.length || '',
        reference.width || '',
        reference.thickness || '',
      ].join(','),
    );

    const refFolderName = this.sanitizeFolderName('0_REFERENCE');
    const refFolder = zip.folder(`images/${refFolderName}`)!;

    for (let i = 0; i < reference.images.length; i++) {
      const imgUrl = reference.images[i];
      try {
        const originalBlob = await fetch(imgUrl).then((res) => res.blob());
        const imgBlob = await this.resizeImage(originalBlob);
        const ext = this.getFileExtension(imgUrl) || 'jpg';
        const filename = `image_${i + 1}.${ext}`;
        refFolder.file(filename, imgBlob);
      } catch (err) {
        console.warn(`Failed to fetch reference image: ${imgUrl}`, err);
      }
    }

    // --- Product entries ---
    let counter = 1;
    for (const product of products) {
      const {
        name,
        store,
        url,
        material,
        length = '',
        width = '',
        thickness = '',
      } = product.description;

      const exportId = counter++;
      const folderName = this.sanitizeFolderName(`${exportId}_${name}`);
      const productFolder = zip.folder(`images/${folderName}`)!;

      for (let i = 0; i < product.images.length; i++) {
        const imgUrl = product.images[i];
        try {
          const originalBlob = await fetch(imgUrl).then((res) => res.blob());
          const imgBlob = await this.resizeImage(originalBlob);
          const ext = this.getFileExtension(imgUrl) || 'jpg';
          const filename = `image_${i + 1}.${ext}`;
          productFolder.file(filename, imgBlob);
        } catch (err) {
          console.warn(`Failed to fetch image: ${imgUrl}`, err);
        }
      }

      csvRows.push(
        [
          exportId,
          `"${name}"`,
          `"${store}"`,
          `"${url}"`,
          `"${material}"`,
          length,
          width,
          thickness,
        ].join(','),
      );
    }

    zip.file('products.csv', csvRows.join('\n'));
    return zip.generateAsync({ type: 'blob' });
  }

  async resizeImage(blob: Blob, maxSize: number = 600): Promise<Blob> {
    const img = await createImageBitmap(blob);
    const { width, height } = img;

    const scale = Math.min(maxSize / width, maxSize / height, 1); // avoid upscaling
    const targetW = Math.round(width * scale);
    const targetH = Math.round(height * scale);

    const canvas = new OffscreenCanvas(targetW, targetH);
    const ctx = canvas.getContext('2d')!;
    ctx.drawImage(img, 0, 0, targetW, targetH);

    return await canvas.convertToBlob({ type: 'image/jpeg', quality: 0.85 });
  }

  private sanitizeFolderName(name: string): string {
    return name
      .replace(/[\/\\?%*:|"<>]/g, '') // illegal characters
      .replace(/\s+/g, '_') // spaces to underscores
      .replace(/_+/g, '_') // collapse underscores
      .toLowerCase();
  }

  private getFileExtension(url: string): string | null {
    const match = url.match(/\.(jpg|jpeg|png|gif|webp)(\?.*)?$/i);
    return match ? match[1].toLowerCase() : null;
  }
}
