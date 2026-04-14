/**
 * Original API Adapter
 * 
 * This adapter bridges the React app's expected API interface with the original 
 * API endpoints documented in current-api-endpoints.md. It transforms request/response
 * data between the two formats.
 */

import { apiClient } from '../client';
import { withAuthHeaders } from '@/lib/auth/auth';
import type { K9Response } from '@/lib/auth/types';
import type { Report, Product, ProductIndex, ProductImage } from '@/types/report';
import { encodeReportTitle, decodeReportId, sanitizeFilename } from '@/lib/utils/jobIdentifiers';

// Types for the original API
interface OriginalApiMaterial {
  type: string;
  material: string;
  length: number;
  width: number;
  thickness: number | null;
  images: string[];
}

interface OriginalApiSearchRequest {
  select_mode: 'color' | 'pattern';
  type_: {
    type: number;
    material: number;
    missing: boolean;
  };
  shape: {
    length?: number;
    width?: number;
    thickness?: number;
    missing: boolean;
  };
  color: {
    primary?: number;
    secondary?: number;
    tertiary?: number;
    missing: boolean;
  };
  pattern: {
    primary?: number;
    secondary?: number;
    tertiary?: number;
    missing: boolean;
  };
}

interface OriginalApiSearchResult {
  id: string;
  match: number;
  images: string[];
  scores: {
    shape: {
      length: number | null;
      width: number | null;
      thickness: number | null;
    };
    color: {
      primary: number | null;
      secondary: number | null;
      tertiary: number | null;
    };
    pattern: {
      primary: number | null;
      secondary: number | null;
      tertiary: number | null;
    };
  };
  description?: {
    store: string;
    name: string;
    url: string;
    material: string;
    length: number | null;
    width: number | null;
    thickness: number | null;
  };
}

// New types for /report endpoints
interface OriginalApiJobListing {
  job: string;
  created: string;
  reference: string; // Single presigned URL instead of full material data
}

interface OriginalApiFavoriteProduct {
  id: string;
  match: number;
  images: string[];
  scores: {
    shape: {
      length: number | null;
      width: number | null;
      thickness: number | null;
    };
    color: {
      primary: number | null;
      secondary: number | null;
      tertiary: number | null;
    };
    pattern: {
      primary: number | null;
      secondary: number | null;
      tertiary: number | null;
    };
  };
  description: {
    store: string;
    name: string;
    url: string;
    material: string;
    length: number | null;
    width: number | null;
    thickness: number | null;
  };
}

/**
 * Capitalize first letter of a string
 */
function capitalize(str: string): string {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Convert centimeters to inches and round to 1 decimal place
 */
function cmToInches(cm: number): number {
  return Math.round((cm / 2.54) * 10) / 10;
}

/**
 * Convert dimensions from React app units (inches for length/width, mm for thickness)
 * to original API expected units (inches for length/width, mm for thickness)
 * Note: The original API expects dimensions in inches, NOT cm
 */
function convertDimensionsToOriginalApi(reactDimensions: {
  length?: { val: number; unit: string } | undefined;
  width?: { val: number; unit: string } | undefined;
  thickness?: { val: number; unit: string } | undefined;
}) {
  return {
    length: reactDimensions.length?.val || undefined,  // Keep inches as inches
    width: reactDimensions.width?.val || undefined,    // Keep inches as inches
    thickness: reactDimensions.thickness?.val || undefined, // mm stays as mm
  };
}

/**
 * Convert dimensions from reference material (inches for length/width, mm for thickness)
 * to React app expected units (inches for length/width, mm for thickness)
 * Reference materials are already in the correct units!
 */
function convertReferenceDimensions(referenceDimensions: {
  length?: number | null;
  width?: number | null;
  thickness?: number | null;
}) {
  return {
    length: referenceDimensions.length ? { val: referenceDimensions.length, unit: 'in' as const } : undefined,
    width: referenceDimensions.width ? { val: referenceDimensions.width, unit: 'in' as const } : undefined,
    thickness: referenceDimensions.thickness ? { val: referenceDimensions.thickness, unit: 'mm' as const } : undefined,
  };
}

/**
 * Convert dimensions from original API units (cm for length/width, mm for thickness)
 * to React app expected units (inches for length/width, mm for thickness)
 */
function convertDimensions(originalDimensions: {
  length?: number | null;
  width?: number | null;
  thickness?: number | null;
}) {
  return {
    length: originalDimensions.length ? { val: cmToInches(originalDimensions.length), unit: 'in' as const } : undefined,
    width: originalDimensions.width ? { val: cmToInches(originalDimensions.width), unit: 'in' as const } : undefined,
    thickness: originalDimensions.thickness ? { val: originalDimensions.thickness, unit: 'mm' as const } : undefined,
  };
}

/**
 * Transform Product reference from React app format to original API format
 */
function transformProductToOriginalFormat(product: Product): OriginalApiMaterial {
  const primaryFormat = product.formats[0];
  
  // Convert dimensions from React app units to original API units
  const convertedDimensions = convertDimensionsToOriginalApi({
    length: primaryFormat?.length,
    width: primaryFormat?.width,
    thickness: primaryFormat?.thickness
  });
  
  return {
    type: (product.category.type || 'tile').toLowerCase(),
    material: (product.category.material || 'ceramic').toLowerCase(),
    length: convertedDimensions.length || 12, // fallback to 12 inches if not provided
    width: convertedDimensions.width || 6,    // fallback to 6 inches if not provided
    thickness: convertedDimensions.thickness || null,
    images: product.images.map(img => {
      // Extract filename from URL for original API
      if (img.url.startsWith('data:') || img.url.startsWith('blob:')) {
        // For data URLs or blobs, generate a filename
        return sanitizeFilename(`${img.id}.jpg`);
      }
      try {
        const url = new URL(img.url);
        const filename = url.pathname.split('/').pop() || `${img.id}.jpg`;
        return sanitizeFilename(filename);
      } catch {
        // If URL parsing fails, use the image ID
        return sanitizeFilename(`${img.id}.jpg`);
      }
    })
  };
}

/**
 * Transform original API search result to React app Product format
 */
function transformSearchResultToProduct(result: OriginalApiSearchResult): ProductIndex {
  return {
    id: result.id,
    brand: result.description?.store || 'Unknown',
    model: result.description?.name || `Material ${result.id}`,
    image: result.images[0] || '',
    match: result.match,
    analysis: {
      color: {
        primary: {
          vector: [
            result.scores.color.primary || 0,
            result.scores.color.secondary || 0
          ],
          similarity: 1 - (result.scores.color.primary || 0) // Convert similarity to distance
        },
        secondary: {
          vector: [
            result.scores.color.secondary || 0,
            result.scores.color.tertiary || 0
          ],
          similarity: 1 - (result.scores.color.secondary || 0) // Convert similarity to distance
        }
      },
      pattern: {
        primary: {
          vector: [
            result.scores.pattern.primary || 0,
            result.scores.pattern.secondary || 0
          ],
          similarity: 1 - (result.scores.pattern.primary || 0) // Convert similarity to distance
        },
        secondary: {
          vector: [
            result.scores.pattern.secondary || 0,
            result.scores.pattern.tertiary || 0
          ],
          similarity: 1 - (result.scores.pattern.secondary || 0) // Convert similarity to distance
        }
      },
      // Preserve API-provided match value directly.
      similarity: result.match
    }
  };
}

/**
 * Transform original API search result to full React app Product format
 */
function transformSearchResultToFullProduct(result: OriginalApiSearchResult): Product {
  const productImages: ProductImage[] = result.images.map((imageUrl, index) => ({
    id: `${result.id}_img${index + 1}`,
    url: imageUrl
  }));

  const dimensions = convertDimensions({
    length: result.description?.length,
    width: result.description?.width,
    thickness: result.description?.thickness
  });

  return {
    id: result.id,
    brand: result.description?.store || 'Unknown',
    model: result.description?.name || `Material ${result.id}`,
    images: productImages,
    category: {
      type: 'Tile', // Default type, capitalized
      material: capitalize(result.description?.material || 'ceramic'),
    },
    formats: [{
      length: dimensions.length,
      width: dimensions.width,
      thickness: dimensions.thickness,
      vendors: [{
        sku: `${result.id}-001`,
        store: result.description?.store || 'Unknown',
        name: result.description?.name || `Material ${result.id}`,
        url: result.description?.url || '#',
        discontinued: false
      }]
    }],
    analysis: {
      color: {
        primary: {
          vector: [
            result.scores.color.primary || 0,
            result.scores.color.secondary || 0
          ],
          similarity: 1 - (result.scores.color.primary || 0) // Convert similarity to distance
        },
        secondary: {
          vector: [
            result.scores.color.secondary || 0,
            result.scores.color.tertiary || 0
          ],
          similarity: 1 - (result.scores.color.secondary || 0) // Convert similarity to distance
        }
      },
      pattern: {
        primary: {
          vector: [
            result.scores.pattern.primary || 0,
            result.scores.pattern.secondary || 0
          ],
          similarity: 1 - (result.scores.pattern.primary || 0) // Convert similarity to distance
        },
        secondary: {
          vector: [
            result.scores.pattern.secondary || 0,
            result.scores.pattern.tertiary || 0
          ],
          similarity: 1 - (result.scores.pattern.secondary || 0) // Convert similarity to distance
        }
      },
      // Preserve API-provided match value directly.
      similarity: result.match
    }
  };
}

/**
 * Transform original API favorite product to React app Product format
 */
function transformFavoriteToProduct(favorite: OriginalApiFavoriteProduct): Product {
  const productImages: ProductImage[] = favorite.images.map((imageUrl, index) => ({
    id: `${favorite.id}_img${index + 1}`,
    url: imageUrl
  }));

  const dimensions = convertDimensions({
    length: favorite.description.length,
    width: favorite.description.width,
    thickness: favorite.description.thickness
  });

  return {
    id: favorite.id,
    brand: favorite.description.store || 'Unknown',
    model: favorite.description.name || `Material ${favorite.id}`,
    images: productImages,
    category: {
      type: 'Tile', // Default type, capitalized
      material: capitalize(favorite.description.material),
    },
    formats: [{
      length: dimensions.length,
      width: dimensions.width,
      thickness: dimensions.thickness,
      vendors: [{
        sku: `${favorite.id}-001`,
        store: favorite.description.store,
        name: favorite.description.name,
        url: favorite.description.url,
        discontinued: false
      }]
    }],
    analysis: {
      color: {
        primary: {
          vector: [
            favorite.scores.color.primary || 0,
            favorite.scores.color.secondary || 0
          ],
          similarity: 1 - (favorite.scores.color.primary || 0) // Convert similarity to distance
        },
        secondary: {
          vector: [
            favorite.scores.color.secondary || 0,
            favorite.scores.color.tertiary || 0
          ],
          similarity: 1 - (favorite.scores.color.secondary || 0) // Convert similarity to distance
        }
      },
      pattern: {
        primary: {
          vector: [
            favorite.scores.pattern.primary || 0,
            favorite.scores.pattern.secondary || 0
          ],
          similarity: 1 - (favorite.scores.pattern.primary || 0) // Convert similarity to distance
        },
        secondary: {
          vector: [
            favorite.scores.pattern.secondary || 0,
            favorite.scores.pattern.tertiary || 0
          ],
          similarity: 1 - (favorite.scores.pattern.secondary || 0) // Convert similarity to distance
        }
      },
      // Use the match score from the API response directly.
      similarity: favorite.match
    }
  };
}
function createFullProductFromOriginal(
  material: OriginalApiMaterial, 
  reportId: string,
  materialId: string
): Product {
  const productImages: ProductImage[] = material.images.map((imageUrl, index) => ({
    id: `${materialId}_img${index + 1}`,
    url: imageUrl
  }));

  // Reference materials have length/width in inches already, thickness in mm
  const dimensions = convertReferenceDimensions({
    length: material.length,
    width: material.width,
    thickness: material.thickness
  });

  return {
    id: materialId,
    brand: 'Unknown', // Original API doesn't provide brand
    model: `${capitalize(material.type)} ${capitalize(material.material)}`,
    images: productImages,
    category: {
      type: capitalize(material.type),
      material: capitalize(material.material),
    },
    formats: [{
      length: dimensions.length,
      width: dimensions.width,
      thickness: dimensions.thickness,
      vendors: [{
        sku: `${materialId}-001`,
        store: 'Material Database',
        name: `${capitalize(material.type)} ${capitalize(material.material)}`,
        url: '#',
        discontinued: false
      }]
    }]
  };
}

export class OriginalApiAdapter {
  /**
   * Create a "report" (job) in the original API
   * This corresponds to PUT /fetch/{job} in the original API
   */
  static async createReport(title: string, reference: Product): Promise<K9Response<{ id: string; runId?: string }>> {
    // Encode the title to use as job identifier
    const jobId = encodeReportTitle(title);
    
    try {
      // First, upload images to album and collect their filenames
      const uploadedImages: string[] = [];
      
      console.log(`[API] Creating job with ID: ${jobId}`);
      console.log(`[API] Need to upload ${reference.images.length} images`);
      
      for (const [index, image] of reference.images.entries()) {
        if (image.url.startsWith('data:') || image.url.startsWith('blob:')) {
          // Convert data URL or blob URL to actual image data
          try {
            console.log(`[API] Processing image ${index + 1}/${reference.images.length}: ${image.id}`);
            const response = await fetch(image.url);
            const imageBlob = await response.blob();
            
            // Generate a unique filename for this image (only the actual image, not mask)
            let extension = 'jpg'; // default extension
            if (imageBlob.type) {
              const mimeType = imageBlob.type.toLowerCase();
              if (mimeType.includes('png')) extension = 'png';
              else if (mimeType.includes('jpeg') || mimeType.includes('jpg')) extension = 'jpg';
              else if (mimeType.includes('webp')) extension = 'webp';
              else if (mimeType.includes('gif')) extension = 'gif';
            }
            
            // Create a simple, clean filename using index - fuck sanitizeFilename
            const finalFilename = `img${index}.${extension}`;
            console.log(`[API] Generated filename: "${finalFilename}" from index: ${index} and extension: "${extension}"`);
            
            console.log(`[API] Uploading image as: ${finalFilename} (${Math.round(imageBlob.size / 1024)}KB)`);
            
            // Upload the image
            const uploadResponse = await this.uploadImage(jobId, finalFilename, imageBlob);
            
            if (uploadResponse.status === 200) {
              uploadedImages.push(finalFilename);
              console.log(`[API] Successfully uploaded: ${finalFilename}`);
            } else {
              console.warn(`[API] Failed to upload image ${finalFilename}: ${uploadResponse.error}`);
              console.warn(`[API] Continuing without this image...`);
              // Continue with other images even if one fails
              // For now, we'll try to proceed without the failed image
            }
          } catch (uploadError) {
            console.warn(`[API] Error processing image ${index}: ${uploadError}`);
            console.warn(`[API] Continuing without this image...`);
            // Continue with other images even if one fails
          }
        } else {
          // For external URLs, use the original URL as-is
          // The original API might handle external URLs directly
          console.log(`[API] Using external URL for image ${index}: ${image.url}`);
          uploadedImages.push(image.url);
        }
      }
      
      console.log(`[API] Successfully processed ${uploadedImages.length} images:`, uploadedImages);
      
      // Transform product to original API format with uploaded image filenames
      const materialData = transformProductToOriginalFormat(reference);
      
      // Update the material data with the uploaded image filenames
      if (materialData.images && uploadedImages.length > 0) {
        materialData.images = uploadedImages;
        console.log(`[API] Updated material data with ${uploadedImages.length} image filenames`);
      } else {
        console.warn(`[API] No images were successfully uploaded. Proceeding with original image URLs.`);
        // If no images were uploaded, keep the original URLs as fallback
        // The original API might be able to handle external URLs or we might need to handle this differently
      }
      
      console.log(`[API] Creating job with material data:`, JSON.stringify(materialData, null, 2));
      
      // Create the job with material data
      const response = await apiClient.put<string>(`/fetch/${jobId}`, materialData);
      
      if (response.status === 200) {
        return {
          status: 201, // Translate to 201 for creation
          body: { 
            id: jobId,
            runId: response.body // The run ID from the original API
          },
          error: undefined
        };
      }
      
      return {
        status: response.status,
        body: { id: '' },
        error: response.error || 'Failed to create report'
      };
    } catch (error) {
      return {
        status: 500,
        body: { id: '' },
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get report data from original API
   * This corresponds to GET /fetch/{job} in the original API
   */
  static async getReport(reportId: string): Promise<K9Response<OriginalApiMaterial>> {
    return apiClient.get<OriginalApiMaterial>(`/fetch/${reportId}`);
  }

  /**
   * Search for similar materials using the original API
   * This corresponds to POST /fetch/{job} in the original API
   */
  static async searchSimilarMaterials(
    reportId: string, 
    filters?: any,
    start: number = 0
  ): Promise<K9Response<OriginalApiSearchResult[]>> {
    // Build search thresholds from filters or use defaults
    // These are distance metrics where lower values mean more similar
    // For example: 90% similarity = 0.1 threshold, 80% similarity = 0.2 threshold
    const searchRequest: OriginalApiSearchRequest = {
      select_mode: filters?.similarity?.selectMode === 'pattern' ? 'pattern' : 'color',
      type_: {
        type: 0.2,  // 80% similarity for type matching
        material: 0.2,  // 80% similarity for material matching
        missing: true
      },
      shape: {
        missing: true
      },
      color: {
        missing: true
      },
      pattern: {
        missing: true
      }
    };

    // Add shape properties only if they have values
    if (filters?.shape?.length) {
      searchRequest.shape.length = filters.shape.length;
    }
    if (filters?.shape?.width) {
      searchRequest.shape.width = filters.shape.width;
    }
    if (filters?.shape?.thickness) {
      searchRequest.shape.thickness = filters.shape.thickness;
    }

    // Include start parameter in the request if provided
    if (start > 0) {
      return apiClient.post<OriginalApiSearchResult[]>(`/fetch/${reportId}?start=${start}`, searchRequest);
    } else {
      return apiClient.post<OriginalApiSearchResult[]>(`/fetch/${reportId}`, searchRequest);
    }
  }

  /**
   * Upload image to job album
   * This corresponds to PUT /fetch/{job}/album/{filename} in the original API
   */
  static async uploadImage(
    reportId: string, 
    filename: string, 
    imageData: Blob | ArrayBuffer
  ): Promise<K9Response<void>> {
    return withAuthHeaders(async (authHeaders) => {
      try {
        // Get the base URL from environment or use the client's base URL
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://824xuvy567.execute-api.us-east-2.amazonaws.com/securek9';
        const uploadUrl = `${baseUrl}/fetch/${reportId}/album/${filename}`;
        
        console.log(`[API] Uploading to: ${uploadUrl}`);
        console.log(`[API] Auth headers:`, JSON.stringify(authHeaders, null, 2));
        console.log(`[API] Content-Type: ${imageData instanceof Blob ? imageData.type : 'application/octet-stream'}`);
        console.log(`[API] Data size: ${imageData instanceof Blob ? imageData.size : imageData.byteLength} bytes`);
        console.log(`[API] Filename: ${filename}`);
        
        const requestHeaders = {
          ...authHeaders, // Include authentication headers
          'Content-Type': imageData instanceof Blob ? imageData.type : 'application/octet-stream'
        };
        
        console.log(`[API] Final request headers:`, JSON.stringify(requestHeaders, null, 2));
        
        const response = await fetch(uploadUrl, {
          method: 'PUT',
          body: imageData,
          headers: requestHeaders
        });

        console.log(`[API] Upload response status: ${response.status} ${response.statusText}`);

        if (response.ok) {
          return {
            status: 200,
            body: undefined,
            error: undefined
          };
        }

        // Try to get more detailed error information from the response body
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const responseText = await response.text();
          if (responseText) {
            errorMessage += ` - ${responseText}`;
          }
        } catch {
          // Ignore errors reading response body
        }

        console.error(`[API] Upload failed: ${errorMessage}`);

        return {
          status: response.status,
          body: undefined,
          error: errorMessage
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed';
        console.error(`[API] Upload exception:`, error);
        return {
          status: 500,
          body: undefined,
          error: errorMessage
        };
      }
    });
  }

  /**
   * Get all reports/jobs for the authenticated user
   * This corresponds to GET /report in the original API
   */
  static async listAllReports(): Promise<K9Response<OriginalApiJobListing[]>> {
    return apiClient.get<OriginalApiJobListing[]>('/report');
  }

  /**
   * Transform an OriginalApiJobListing (from GET /report) to Report<ProductIndex>
   */
  static transformJobListingToReport(jobListing: OriginalApiJobListing): Report<ProductIndex> {
    const referenceMaterial: ProductIndex = {
      id: `${jobListing.job}-reference`,
      brand: 'Unknown',
      model: jobListing.job,
      image: jobListing.reference
    };

    return {
      id: jobListing.job,
      title: decodeReportId(jobListing.job), // Decode the title from the job ID
      author: 'current-user', // We don't have author in the listing
      date: new Date(jobListing.created).toISOString(),
      reference: referenceMaterial,
      favorites: [] // No favorites in the listing data
    };
  }

  /**
   * Get favorites for a specific job
   * This corresponds to GET /report/{job}/favorites in the original API
   */
  static async getFavorites(reportId: string): Promise<K9Response<OriginalApiFavoriteProduct[]>> {
    return apiClient.get<OriginalApiFavoriteProduct[]>(`/report/${reportId}/favorites`);
  }

  /**
   * Get favorites for a specific job as Product[] format (for frontend consumption)
   * This corresponds to GET /report/{job}/favorites in the original API
   */
  static async getFavoritesAsProducts(reportId: string): Promise<K9Response<Product[]>> {
    const response = await this.getFavorites(reportId);
    
    if (response.status === 200) {
      const products = response.body.map(favorite => transformFavoriteToProduct(favorite));
      return {
        status: 200,
        body: products,
        error: undefined
      };
    }
    
    return {
      status: response.status,
      body: [],
      error: response.error
    };
  }

  /**
   * Replace all favorites for a specific job
   * This corresponds to PUT /report/{job}/favorites in the original API
   */
  static async updateFavorites(reportId: string, productIds: string[]): Promise<K9Response<{ product_ids: string[] }>> {
    return apiClient.put<{ product_ids: string[] }>(`/report/${reportId}/favorites`, {
      product_ids: productIds
    });
  }

  /**
   * Toggle a single favorite for a specific job
   * This corresponds to POST /report/{job}/favorites in the original API
   */
  static async toggleFavorite(reportId: string, productId: string): Promise<K9Response<{ product_ids: string[] }>> {
    return apiClient.post<{ product_ids: string[] }>(`/report/${reportId}/favorites`, {
      product_id: productId
    });
  }

  /**
   * Get a single product by ID from the new product endpoint
   * This corresponds to GET /fetch/{job}/product/{id} in the original API
   */
  static async getProductById(reportId: string, productId: string): Promise<K9Response<Product>> {
    try {
      const response = await apiClient.get<OriginalApiSearchResult>(`/fetch/${reportId}/product/${productId}`);
      
      if (response.status === 200) {
        const product = transformSearchResultToFullProduct(response.body);
        return {
          status: 200,
          body: product,
          error: undefined
        };
      }
      
      return {
        status: response.status,
        body: null as any,
        error: response.error || 'Product not found'
      };
    } catch (error) {
      return {
        status: 500,
        body: null as any,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get a single product by ID from search results
   * Since the original API doesn't have a direct "get product by ID" endpoint,
   * this searches all results to find the specific product
   * @deprecated Use getProductById instead - this method is expensive
   */
  static async getProductFromSearch(reportId: string, productId: string): Promise<K9Response<Product>> {
    // Search with very permissive filters to get all results
    const searchRequest: OriginalApiSearchRequest = {
      type_: { type: 0.1, material: 0.1, missing: true },
      shape: { length: 0.1, width: 0.1, thickness: 0.1, missing: true },
      color: { primary: 0.1, secondary: 0.1, tertiary: 0.1, missing: true },
      pattern: { primary: 0.1, secondary: 0.1, tertiary: 0.1, missing: true }
    };

    try {
      const response = await apiClient.post<OriginalApiSearchResult[]>(`/fetch/${reportId}`, searchRequest);
      
      if (response.status === 200) {
        // Find the specific product in the search results
        const searchResult = response.body.find(result => result.id === productId);
        
        if (searchResult) {
          const product = transformSearchResultToFullProduct(searchResult);
          return {
            status: 200,
            body: product,
            error: undefined
          };
        } else {
          return {
            status: 404,
            body: null as any,
            error: 'Product not found in search results'
          };
        }
      }
      
      return {
        status: response.status,
        body: null as any,
        error: response.error || 'Failed to search for product'
      };
    } catch (error) {
      return {
        status: 500,
        body: null as any,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}

export { 
  transformProductToOriginalFormat, 
  transformSearchResultToProduct, 
  transformSearchResultToFullProduct,
  createFullProductFromOriginal,
  transformFavoriteToProduct
};