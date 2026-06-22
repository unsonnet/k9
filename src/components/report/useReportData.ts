"use client";

import { useEffect, useState, useRef } from "react";
import type { Report, Product, ProductIndex } from "@/types/report";
import { reportsApi } from "@/lib/api/reports";
import { simulateApiDelay } from "@/data/mockSearchResults";
import type { SearchFilters as SearchFiltersType } from "./SearchFilters";

// Session storage keys
const getFilterStorageKey = (reportId: string) => `report_filters_${reportId}`;
const getResultsStorageKey = (reportId: string) => `report_results_${reportId}`;
const getSearchedStorageKey = (reportId: string) => `report_searched_${reportId}`;

interface UseReportDataProps {
  reportId: string;
}

interface UseReportDataReturn {
  report: Report<Product> | null;
  isLoading: boolean;
  error: string | null;
  searchResults: ProductIndex[];
  isSearching: boolean;
  hasSearched: boolean;
  handleSearch: (filters: SearchFiltersType) => Promise<void>;
  /** Initial favorites from the database (for useFavorites initialization) */
  initialFavorites: string[];
  /** Current search filters state */
  searchFilters: SearchFiltersType | null;
  /** Update search filters */
  setSearchFilters: (filters: SearchFiltersType) => void;
}

export function useReportData({ reportId }: UseReportDataProps): UseReportDataReturn {
  const [report, setReport] = useState<Report<Product> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<ProductIndex[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchFilters, setSearchFilters] = useState<SearchFiltersType | null>(null);
  const isLoadingReportRef = useRef(false); // Use ref to prevent infinite loop

  // Debug: Log hook instantiation with stack trace
  console.log(`[useReportData] Hook instantiated for reportId: ${reportId}`, new Error().stack?.split('\n')[2]);

  // Load persisted data from sessionStorage
  useEffect(() => {
    if (typeof window !== 'undefined' && reportId) {
      try {
        // Load persisted filters
        const storedFilters = sessionStorage.getItem(getFilterStorageKey(reportId));
        if (storedFilters) {
          setSearchFilters(JSON.parse(storedFilters));
        }

        // Load persisted search results
        const storedResults = sessionStorage.getItem(getResultsStorageKey(reportId));
        if (storedResults) {
          setSearchResults(JSON.parse(storedResults));
        }

        // Load persisted search state
        const storedSearched = sessionStorage.getItem(getSearchedStorageKey(reportId));
        if (storedSearched) {
          setHasSearched(JSON.parse(storedSearched));
        }
      } catch (error) {
        console.warn('Failed to load persisted search data:', error);
      }
    }
  }, [reportId]);

  // Persist data to sessionStorage when it changes
  useEffect(() => {
    if (typeof window !== 'undefined' && reportId) {
      if (searchFilters) {
        sessionStorage.setItem(getFilterStorageKey(reportId), JSON.stringify(searchFilters));
      }
    }
  }, [searchFilters, reportId]);

  useEffect(() => {
    if (typeof window !== 'undefined' && reportId) {
      sessionStorage.setItem(getResultsStorageKey(reportId), JSON.stringify(searchResults));
    }
  }, [searchResults, reportId]);

  useEffect(() => {
    if (typeof window !== 'undefined' && reportId) {
      sessionStorage.setItem(getSearchedStorageKey(reportId), JSON.stringify(hasSearched));
    }
  }, [hasSearched, reportId]);

  useEffect(() => {
    const loadReport = async () => {
      // Prevent multiple concurrent calls
      if (isLoadingReportRef.current || !reportId) return;
      
      try {
        isLoadingReportRef.current = true;
        setIsLoading(true);
        setError(null);
        
        console.log(`[useReportData] Loading report: ${reportId}`);
        
        // Use the new getFullReport function
        const foundReport = await reportsApi.getFullReport(reportId, 'useReportData');
        
        if (!foundReport) {
          setError("Report not found");
          return;
        }

        setReport(foundReport);
        console.log(`[useReportData] Successfully loaded report: ${reportId}`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load report");
      } finally {
        setIsLoading(false);
        isLoadingReportRef.current = false;
      }
    };

    loadReport();
  }, [reportId]);

  const updateSearchFilters = (filters: SearchFiltersType) => {
    setSearchFilters(filters);
    // sessionStorage will be updated by the useEffect above
  };

  const handleSearch = async (filters: SearchFiltersType) => {
    setIsSearching(true);
    setHasSearched(true); // Mark that a search has been performed
    setSearchFilters(filters); // Store the filters used for this search
    
    try {
      if (!report) {
        console.warn("No report loaded, cannot search");
        return;
      }

      // Check if real API should be used
      const USE_REAL_API = process.env.NEXT_PUBLIC_USE_REAL_API !== 'false';
      
      if (USE_REAL_API) {
        try {
          console.log('[API] Starting search for reportId:', report.id);
          console.log('[API] Search filters:', filters);
          
          const { reportsApiService } = await import("@/lib/api/reportsApi");
          
          // Transform component SearchFilters to API SearchFilters format
          const apiFilters = {
            brand: filters.brand && filters.brand.length > 0 ? filters.brand : undefined,
            category: {
              type: filters.categories.type?.[0], // Take first type if multiple
              material: filters.categories.material?.[0], // Take first material if multiple
              look: filters.categories.look,
              texture: filters.categories.texture,
              finish: filters.categories.finish,
              edge: filters.categories.edge,
            },
            similarity: {
              selectMode: filters.selectMode,
            },
            shape: {
              length: filters.maxLengthDiff,
              width: filters.maxWidthDiff,
              thickness: filters.maxThicknessDiff,
            }
          };
          
          console.log('[API] Transformed API filters:', apiFilters);
          
          const response = await reportsApiService.searchProducts(report.id, {
            filters: apiFilters,
            page: 1,
            limit: 50,
          });
          
          console.log('[API] Search response status:', response.status);
          console.log('[API] Search response:', response);
          
          if (response.status === 200) {
            console.log('[API] Search successful, found', response.body.products.length, 'products');
            setSearchResults(response.body.products);
            return; // Exit early on success
          } else {
            console.error("Search failed:", response.error);
            throw new Error(response.error || 'Search failed');
          }
        } catch (error) {
          console.error('[API] Error during search:', error);
          console.log('[API] Falling back to mock implementation');
        }
      }

      // Mock search results - fallback when real API fails or is disabled
      await simulateApiDelay(1000); // Simulate API call
      
      // Get search results specific to this report and its reference product
      const { getMockSearchResults } = await import("@/data/mockSearchResults");
      const resultsForReport = getMockSearchResults(report.id, report.reference.id);
      
      // Return a random subset of results (0 to all results) to simulate filtering
      const totalResults = resultsForReport.length;
      const randomCount = Math.floor(Math.random() * (totalResults + 1)); // 0 to totalResults inclusive
      
      // Shuffle the array and take the first randomCount items
      const shuffled = [...resultsForReport].sort(() => Math.random() - 0.5);
      const randomResults = shuffled.slice(0, randomCount);
      
      setSearchResults(randomResults);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setIsSearching(false);
    }
  };

  return {
    report,
    isLoading,
    error,
    searchResults,
    isSearching,
    hasSearched,
    handleSearch,
    initialFavorites: report?.favorites || [],
    searchFilters,
    setSearchFilters: updateSearchFilters
  };
}