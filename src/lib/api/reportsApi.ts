/**
 * Reports API Service - Updated to use Original API Adapter
 * 
 * This service now uses the original API endpoints through adapter functions
 * that translate between the React app's expected interface and the original API format.
 */

import { OriginalApiAdapter, transformSearchResultToProduct, createFullProductFromOriginal, transformFavoriteToProduct } from './adapters/originalApiAdapter';
import { decodeReportId } from '@/lib/utils/jobIdentifiers';
import type { Report, Product, ProductIndex } from '@/types/report';
import type { K9Response } from '@/lib/auth/types';

export interface CreateReportRequest {
  title: string;
  reference: Product;
}

export interface CreateReportResponse {
  id: string;
  title: string;
  author: string;
  date: string;
}

export interface ListReportsResponse {
  reports: Report<ProductIndex>[];
  total: number;
  limit: number;
  next_cursor: string | null;  // DynamoDB pagination cursor
  has_more: boolean;          // Whether there are more results
}

export interface SearchFilters {
  category?: {
    type?: string;
    material?: string;
    look?: string[];
    texture?: string[];
    finish?: string[];
    edge?: string[];
  };
  brand?: string[];
  priceRange?: {
    min?: number;
    max?: number;
  };
  similarity?: {
    selectMode: 'color' | 'pattern';
  };
  shape?: {
    length?: number;
    width?: number;
    thickness?: number;
  };
}

export interface SearchProductsRequest {
  filters: SearchFilters;
  page?: number;
  limit?: number;
}

export interface SearchProductsResponse {
  products: ProductIndex[];
  total: number;
  page: number;
  limit: number;
}

export class ReportsApiService {
  /**
   * 1. Get list of reports associated with the current user
   * Now uses original API: GET /report
   */
  static async listReports(limit: number = 20, _cursor?: string): Promise<K9Response<ListReportsResponse>> {
    const response = await OriginalApiAdapter.listAllReports();
    
    if (response.status === 200) {
      // Transform original API job listings to Report<ProductIndex> for list view
      const reports: Report<ProductIndex>[] = response.body.map(jobListing => 
        OriginalApiAdapter.transformJobListingToReport(jobListing)
      );
      
      return {
        status: 200,
        body: {
          reports,
          total: reports.length,
          limit,
          next_cursor: null, // No pagination in simplified response
          has_more: false   // No pagination in simplified response
        },
        error: undefined
      };
    }
    
    return {
      status: response.status,
      body: {
        reports: [],
        total: 0,
        limit,
        next_cursor: null,
        has_more: false
      },
      error: response.error
    };
  }

  /**
   * 2. Create a new report and get back report ID
   * Uses original API: PUT /fetch/{job}
   */
  static async createReport(data: CreateReportRequest): Promise<K9Response<CreateReportResponse>> {
    const response = await OriginalApiAdapter.createReport(data.title, data.reference);
    
    if (response.status === 201) {
      return {
        status: 201,
        body: {
          id: response.body.id,
          title: data.title,
          author: 'current-user', // TODO: Get from auth context
          date: new Date().toISOString()
        },
        error: undefined
      };
    }
    
    return {
      status: response.status,
      body: {
        id: '',
        title: '',
        author: '',
        date: ''
      },
      error: response.error
    };
  }

  /**
   * 3. Get a specific report by ID
   * Now uses original API: GET /fetch/{job} directly and fetches favorites
   */
  static async getReport(reportId: string): Promise<K9Response<Report<Product>>> {
    console.log('[API] ReportsApiService.getReport called for reportId:', reportId);
    
    try {
      // Only fetch the report data, NOT favorites (let the hook handle favorites)
      const fullJobResponse = await OriginalApiAdapter.getReport(reportId);
      
      if (fullJobResponse.status !== 200) {
        console.error('[API] Failed to fetch report:', reportId, fullJobResponse.error);
        return {
          status: fullJobResponse.status,
          body: null as any,
          error: fullJobResponse.error || 'Report not found'
        };
      }
      
      // Transform the full material data to a Report<Product>
      const product = createFullProductFromOriginal(
        fullJobResponse.body, 
        reportId, 
        reportId
      );
      
      // Get creation date - we'll need to call a different endpoint or use current date
      const currentDate = new Date().toISOString();
      
      const report: Report<Product> = {
        id: reportId,
        title: decodeReportId(reportId), // Decode the title from the report ID
        author: 'current-user',
        date: currentDate,
        reference: product,
        favorites: [] // Empty - let the hook load favorites separately
      };
      
      console.log('[API] Successfully retrieved report:', reportId);
      return {
        status: 200,
        body: report,
        error: undefined
      };
    } catch (error) {
      console.error('[API] Error fetching report data:', error);
      return {
        status: 500,
        body: null as any,
        error: error instanceof Error ? error.message : 'Failed to load report'
      };
    }
  }

  /**
   * 4. Search for products within a report using filters
   * Uses original API: POST /fetch/{job}
   */
  static async searchProducts(reportId: string, searchRequest: SearchProductsRequest): Promise<K9Response<SearchProductsResponse>> {
    const start = ((searchRequest.page || 1) - 1) * (searchRequest.limit || 20);
    
    const searchResponse = await OriginalApiAdapter.searchSimilarMaterials(
      reportId,
      searchRequest.filters,
      start
    );
    
    if (searchResponse.status === 200) {
      const allProducts = searchResponse.body.map(result => 
        transformSearchResultToProduct(result)
      );
      
      // Deduplicate by ID - keep only the first occurrence of each ID
      const seenIds = new Set<string>();
      const products = allProducts.filter(product => {
        if (seenIds.has(product.id)) {
          console.log(`[API] Removing duplicate product ID: ${product.id}`);
          return false;
        }
        seenIds.add(product.id);
        return true;
      });
      
      if (products.length !== allProducts.length) {
        console.log(`[API] Deduplication: ${allProducts.length} → ${products.length} products (removed ${allProducts.length - products.length} duplicates)`);
      }
      
      return {
        status: 200,
        body: {
          products,
          total: products.length, // Original API doesn't provide total count
          page: searchRequest.page || 1,
          limit: searchRequest.limit || 20
        },
        error: undefined
      };
    }
    
    return {
      status: searchResponse.status,
      body: {
        products: [],
        total: 0,
        page: 1,
        limit: 20
      },
      error: searchResponse.error
    };
  }

  /**
   * 5. Get full product details given report ID and product ID
   * Uses the new efficient product endpoint, with fallback to favorites
   */
  static async getProduct(reportId: string, productId: string): Promise<K9Response<Product>> {
    console.log(`[API] Getting product ${productId} from report ${reportId}`);
    
    // First, try the new efficient product endpoint
    const productResponse = await OriginalApiAdapter.getProductById(reportId, productId);
    
    if (productResponse.status === 200) {
      console.log(`[API] Product ${productId} found via product endpoint`);
      return productResponse;
    }
    
    if (productResponse.status === 404) {
      // If not found via product endpoint, try favorites as fallback
      console.log(`[API] Product ${productId} not found via product endpoint, trying favorites...`);
      const favoritesResponse = await OriginalApiAdapter.getFavorites(reportId);
      
      if (favoritesResponse.status === 200) {
        const favoriteProduct = favoritesResponse.body.find(fav => fav.id === productId);
        
        if (favoriteProduct) {
          console.log(`[API] Product ${productId} found in favorites`);
          const product = transformFavoriteToProduct(favoriteProduct);
          return {
            status: 200,
            body: product,
            error: undefined
          };
        }
      }
    }
    
    console.log(`[API] Product ${productId} not found anywhere`);
    return {
      status: 404,
      body: null as any,
      error: 'Product not found'
    };
  }

  /**
   * 6. Update favorite status of a product in a report
   * Now uses original API: POST /report/{job}/favorites
   */
  static async updateFavoriteStatus(reportId: string, productId: string, _isFavorite: boolean): Promise<K9Response<{ success: boolean }>> {
    const response = await OriginalApiAdapter.toggleFavorite(reportId, productId);
    
    if (response.status === 200) {
      return {
        status: 200,
        body: { success: true },
        error: undefined
      };
    }
    
    return {
      status: response.status,
      body: { success: false },
      error: response.error
    };
  }

  /**
   * 7. Sync all favorites for a report (bulk update)
   * Now uses original API: PUT /report/{job}/favorites
   */
  static async syncFavorites(reportId: string, favoriteIds: string[]): Promise<K9Response<{ success: boolean }>> {
    const response = await OriginalApiAdapter.updateFavorites(reportId, favoriteIds);
    
    if (response.status === 200) {
      return {
        status: 200,
        body: { success: true },
        error: undefined
      };
    }
    
    return {
      status: response.status,
      body: { success: false },
      error: response.error
    };
  }

  /**
   * 8. Get favorites as full Product objects with match scores
   * Now uses original API: GET /report/{job}/favorites
   */
  static async getFavorites(reportId: string): Promise<K9Response<Product[]>> {
    const response = await OriginalApiAdapter.getFavoritesAsProducts(reportId);
    
    if (response.status === 200) {
      return {
        status: 200,
        body: response.body,
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
   * 9. Export favorited products as ZIP file
   * Client-side implementation using favorites data
   */
  static async exportFavorites(
    reportId: string, 
    onProgress?: (current: number, total: number, message: string) => void
  ): Promise<K9Response<{ blob: Blob; reportTitle: string }>> {
    try {
      // Get favorites as full Product objects
      const favoritesResponse = await this.getFavorites(reportId);
      if (favoritesResponse.status !== 200) {
        return {
          status: favoritesResponse.status,
          body: null as any,
          error: favoritesResponse.error || 'Failed to fetch favorites'
        };
      }

      // Get report for reference product
      const reportResponse = await this.getReport(reportId);
      if (reportResponse.status !== 200) {
        return {
          status: reportResponse.status,
          body: null as any,
          error: reportResponse.error || 'Failed to fetch report'
        };
      }

      // Use favorites directly as Product objects
      const { exportFavoritesAsZip } = await import('@/lib/utils/export');
      const zipBlob = await exportFavoritesAsZip(
        favoritesResponse.body, // Already Product[] objects
        reportResponse.body.reference,
        reportResponse.body.title,
        {
          onProgress // Pass through the progress callback
        }
      );

      return {
        status: 200,
        body: { blob: zipBlob, reportTitle: reportResponse.body.title },
        error: undefined
      };
    } catch (error) {
      console.error('[API] Export failed:', error);
      return {
        status: 500,
        body: null as any,
        error: error instanceof Error ? error.message : 'Export failed'
      };
    }
  }

  /**
   * Delete a report
   * NOTE: Original API still doesn't have delete functionality
   * TODO: Implement report deletion in backend (DELETE /report/{job})
   */
  static async deleteReport(_reportId: string): Promise<K9Response<{ success: boolean }>> {
    // TODO: Implement report deletion in backend
    console.warn('[API] deleteReport not implemented - need backend delete functionality');
    
    return {
      status: 501,
      body: { success: false },
      error: 'Delete functionality not implemented'
    };
  }

  /**
   * Update report metadata
   * NOTE: Original API still doesn't have update functionality
   * TODO: Implement report metadata updates in backend (PATCH /report/{job})
   */
  static async updateReport(_reportId: string, _updates: Partial<Pick<Report<Product>, 'title'>>): Promise<K9Response<Report<Product>>> {
    // TODO: Implement report metadata updates in backend
    console.warn('[API] updateReport not implemented - need backend update functionality');
    
    return {
      status: 501,
      body: null as any,
      error: 'Update functionality not implemented'
    };
  }
}

export const reportsApiService = ReportsApiService;