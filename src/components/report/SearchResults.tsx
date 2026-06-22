"use client";

import { useRouter } from "next/navigation";
import { Grid, Heart, Package, Search, Download } from "lucide-react";
import { useState, useCallback, useMemo } from "react";
import type { ProductIndex, Product } from "@/types/report";
import { useFavorites } from "@/hooks/useFavorites";
import { ImageWithPlaceholder } from "@/components/ImageWithPlaceholder";

interface SearchResultsProps {
  results: ProductIndex[];
  isLoading: boolean;
  hasSearched: boolean;
  reportId: string;
  referenceProduct?: Product; // Keep as Product since the reference in reports is the full Product
  initialFavorites?: string[]; // Initial favorites from the database
}

interface ViewMode {
  type: "grid" | "favorites";
}

export function SearchResults({ results, isLoading, hasSearched, reportId }: SearchResultsProps) {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<ViewMode["type"]>("grid");
  const [nameFilter, setNameFilter] = useState("");
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState<{ current: number; total: number; message: string } | null>(null);
  const { favorites, isFavorited, toggleFavorite } = useFavorites(reportId, {
    autoClear: true
  });

  const getProductNameText = (product: ProductIndex) => {
    const parts = [];
    if (product.brand) parts.push(product.brand);
    if (product.series) parts.push(product.series);
    if (product.model) parts.push(product.model);
    return parts.join(' ') || 'Unknown Product';
  };

  const normalizeText = (value: string) => value.toLowerCase().replace(/[^a-z0-9\s-]/g, ' ').replace(/\s+/g, ' ').trim();

  const isWithinEditDistance = (a: string, b: string, maxDistance: number) => {
    const al = a.length;
    const bl = b.length;
    if (Math.abs(al - bl) > maxDistance) return false;
    if (maxDistance === 0) return a === b;

    const prev = new Array(bl + 1);
    const curr = new Array(bl + 1);

    for (let j = 0; j <= bl; j += 1) prev[j] = j;

    for (let i = 1; i <= al; i += 1) {
      curr[0] = i;
      let rowMin = curr[0];

      for (let j = 1; j <= bl; j += 1) {
        const cost = a[i - 1] === b[j - 1] ? 0 : 1;
        curr[j] = Math.min(
          prev[j] + 1,
          curr[j - 1] + 1,
          prev[j - 1] + cost
        );
        if (curr[j] < rowMin) rowMin = curr[j];
      }

      if (rowMin > maxDistance) return false;
      for (let j = 0; j <= bl; j += 1) prev[j] = curr[j];
    }

    return prev[bl] <= maxDistance;
  };

  const fuzzyNameMatch = (name: string, query: string) => {
    const normalizedName = normalizeText(name);
    const normalizedQuery = normalizeText(query);
    if (!normalizedQuery) return true;
    if (!normalizedName) return false;
    if (normalizedName.includes(normalizedQuery)) return true;

    const queryTokens = normalizedQuery.split(' ').filter(Boolean);
    const nameTokens = normalizedName.split(' ').filter(Boolean);

    return queryTokens.every((queryToken) => {
      const maxDistance = Math.max(1, Math.floor(queryToken.length * 0.3));
      return nameTokens.some((nameToken) =>
        nameToken.includes(queryToken) ||
        queryToken.includes(nameToken) ||
        isWithinEditDistance(nameToken, queryToken, maxDistance)
      );
    });
  };

  const formatProductName = (product: ProductIndex) => {
    const brandSeries = [];
    if (product.brand) brandSeries.push(product.brand);
    if (product.series) brandSeries.push(product.series);
    
    const lines = [];
    
    // Brand and series on first line (if they exist)
    if (brandSeries.length > 0) {
      lines.push(
        <div key="brand-series" className="search-result-card__name-line">
          {brandSeries.map((part, index) => (
            <span key={index}>
              {part}
              {index < brandSeries.length - 1 && (
                <span className="search-result-card__separator">›</span>
              )}
            </span>
          ))}
        </div>
      );
    }
    
    // Model on its own line (highlighted)
    if (product.model) {
      lines.push(
        <div key="model" className="search-result-card__name-line">
          {product.model}
        </div>
      );
    }
    
    return lines.length > 0 ? lines : 'Unknown Product';
  };

  const getSimilarity = (product: ProductIndex) => {
    const rawMatch = product.match ?? product.analysis?.similarity;
    if (rawMatch === undefined || rawMatch === null || Number.isNaN(rawMatch)) {
      return 0;
    }

    // API match is a distance score (0 best, 1 worst); invert for UX percentage.
    const clamped = Math.max(0, Math.min(1, rawMatch));
    return Math.round((1 - clamped) * 100);
  };

  const getSimilarityColorClass = (similarity: number) => {
    if (similarity >= 90) return "similarity-excellent";
    if (similarity >= 80) return "similarity-good";
    if (similarity >= 70) return "similarity-fair";
    if (similarity >= 60) return "similarity-poor";
    return "similarity-very-poor";
  };

      const handleProductClick = useCallback((productId: string) => {
    const url = `/fetch?report=${reportId}&product=${productId}`;
    router.push(url);
  }, [reportId, router]);

  const handleFavoriteClick = (e: React.MouseEvent, product: ProductIndex) => {
    e.stopPropagation(); // Prevent triggering product click
    toggleFavorite(product);
  };

  const handleExportFavorites = async () => {
    if (favorites.length === 0) {
      console.warn('No favorites to export');
      alert('Please add some products to favorites before exporting.');
      return;
    }

    if (isLoading) {
      console.warn('Cannot export while searching');
      alert('Please wait for the current search to complete before exporting.');
      return;
    }

    setIsExporting(true);
    setExportProgress({ current: 0, total: 1, message: 'Initializing export...' });
    
    try {
      console.log(`Starting export of ${favorites.length} favorite products...`);
      
      // Use the real API service for export with progress callback
      const { reportsApiService } = await import('@/lib/api/reportsApi');
      const response = await reportsApiService.exportFavorites(
        reportId,
        (current: number, total: number, message: string) => {
          setExportProgress({ current, total, message });
        }
      );
      
      if (response.status === 200) {
        // Create download link for the blob
        setExportProgress({ current: 1, total: 1, message: 'Download starting...' });
        
        const { downloadBlob, createExportFilename } = await import('@/lib/utils/export');
        const filename = createExportFilename(response.body.reportTitle);
        
        downloadBlob(response.body.blob, filename);
        
        console.log(`Export completed successfully: ${filename}`);
        setExportProgress({ current: 1, total: 1, message: 'Export complete!' });
        
        // Clear progress after a short delay
        setTimeout(() => setExportProgress(null), 2000);
      } else {
        throw new Error(response.error || 'Export failed');
      }
      
    } catch (error) {
      console.error('Export failed:', error);
      const errorMessage = error instanceof Error ? error.message : 'Export failed';
      alert(`Export failed: ${errorMessage}. Please try again.`);
      setExportProgress(null);
    } finally {
      setIsExporting(false);
    }
  };

  // Get the current products to display based on view mode
  const displayProducts =
    viewMode === "favorites"
      ? favorites.map((fav) => {
          // Keep API order for result-backed values and reuse API match when available.
          const resultMatch = results.find((r) => r.id === fav.id);
          const finalAnalysis = resultMatch?.analysis || fav.analysis;

          return {
            id: fav.id,
            brand: fav.brand,
            series: fav.series,
            model: fav.model,
            image: fav.image,
            match: resultMatch?.match ?? fav.match,
            analysis: finalAnalysis,
          } as ProductIndex;
        })
      : results;

  const filteredDisplayProducts = useMemo(() => {
    if (!nameFilter.trim()) return displayProducts;
    return displayProducts.filter((product) =>
      fuzzyNameMatch(getProductNameText(product), nameFilter)
    );
  }, [displayProducts, nameFilter]);

  const hasActiveNameFilter = nameFilter.trim().length > 0;
  const totalDisplayCount = displayProducts.length;
  const filteredDisplayCount = filteredDisplayProducts.length;

  const countLabel = (() => {
    if (viewMode === "favorites") {
      if (hasActiveNameFilter) {
        return `${filteredDisplayCount}/${totalDisplayCount} favorites`;
      }
      return `${filteredDisplayCount} ${filteredDisplayCount === 1 ? "favorite" : "favorites"}`;
    }

    if (hasActiveNameFilter) {
      return `${filteredDisplayCount}/${totalDisplayCount} products found`;
    }

    return `${filteredDisplayCount} ${filteredDisplayCount === 1 ? "product found" : "products found"}`;
  })();

  if (isLoading) {
    return (
      <div className="search-results">
        {/* Header with view controls - same structure as main component */}
        <div className="search-filters__header">
          <div className="search-results__title-section">
            <h3 className="search-filters__title">
              <Search className="w-4 h-4" />
              Results
            </h3>
            <span className="search-results__count">Searching...</span>
          </div>
          
          <div className="search-results__header-actions">
            {/* Export button - always visible, disabled when searching or no favorites */}
            <button
              onClick={handleExportFavorites}
              disabled={true} // Always disabled during loading
              className="search-results__export-btn"
              aria-label="Export favorites"
              title="Cannot export while searching"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            
            <div className="search-results__view-controls">
              <button
                disabled
                className={`search-results__view-btn ${
                  viewMode === "grid" ? "search-results__view-btn--active" : ""
                }`}
                aria-label="Grid view"
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                disabled
                className={`search-results__view-btn ${
                  viewMode === "favorites" ? "search-results__view-btn--active" : ""
                }`}
                aria-label="Favorites view"
              >
                <Heart className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
        <div className="search-results__loading">
          <div className="loading-spinner"></div>
          <p>Searching for similar products...</p>
        </div>
      </div>
    );
  }

  if (viewMode === "favorites" && displayProducts.length === 0) {
    return (
      <div className="search-results">
        <div className="search-filters__header">
          <div className="search-results__title-section">
            <h3 className="search-filters__title">
              <Heart className="w-4 h-4" />
              Favorites
            </h3>
            <span className="search-results__count">0 favorites</span>
          </div>
          
          <div className="search-results__header-actions">
            {/* Export button - always visible, disabled when no favorites */}
            <button
              onClick={handleExportFavorites}
              disabled={true} // Always disabled when no favorites
              className="search-results__export-btn"
              aria-label="Export favorites"
              title="No favorites to export"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            
            <div className="search-results__view-controls">
              <button
                onClick={() => setViewMode("grid")}
                disabled={isLoading}
                className="search-results__view-btn"
                aria-label="Grid view"
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode("favorites")}
                disabled={isLoading}
                className="search-results__view-btn search-results__view-btn--active"
                aria-label="Favorites view"
              >
                <Heart className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
        <div className="search-results__empty">
          <Heart className="w-12 h-12 text-gray-400" />
          <h3>No favorites yet</h3>
          <p>Click the heart icon on any product to add it to your favorites.</p>
        </div>
      </div>
    );
  }

  if (viewMode === "grid" && results.length === 0) {
    return (
      <div className="search-results">
        <div className="search-filters__header">
          <div className="search-results__title-section">
            <h3 className="search-filters__title">
              <Search className="w-4 h-4" />
              Results
            </h3>
            <span className="search-results__count">
              {!hasSearched ? "No search performed" : "0 products found"}
            </span>
          </div>
          
          <div className="search-results__header-actions">
            {/* Export button - always visible, disabled when no favorites */}
            <button
              onClick={handleExportFavorites}
              disabled={isExporting || isLoading || favorites.length === 0}
              className="search-results__export-btn"
              aria-label="Export favorites"
              title={
                favorites.length === 0 
                  ? "No favorites to export" 
                  : isLoading 
                  ? "Cannot export while searching" 
                  : isExporting
                  ? (exportProgress ? `${exportProgress.message} (${exportProgress.current}/${exportProgress.total})` : "Exporting...")
                  : "Export favorites as ZIP"
              }
            >
              <Download className="w-4 h-4" />
              {isExporting ? (exportProgress ? `${Math.round((exportProgress.current / exportProgress.total) * 100)}%` : "Exporting...") : "Export"}
            </button>
            
            <div className="search-results__view-controls">
              <button
                onClick={() => setViewMode("grid")}
                disabled={isLoading}
                className="search-results__view-btn search-results__view-btn--active"
                aria-label="Grid view"
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode("favorites")}
                disabled={isLoading}
                className="search-results__view-btn"
                aria-label="Favorites view"
              >
                <Heart className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
        <div className="search-results__empty">
          <Package className="w-12 h-12 text-gray-400" />
          {!hasSearched ? (
            <>
              <h3>No search performed</h3>
              <p>Adjust your filters in the left sidebar and click &quot;Search Similar Products&quot; to find matching products.</p>
            </>
          ) : (
            <>
              <h3>No products found</h3>
              <p>No products match your current search criteria. Try adjusting your filters and search again.</p>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="search-results">
      {/* Header with view controls */}
      <div className="search-filters__header">
        <div className="search-results__title-section">
          <h3 className="search-filters__title">
            {viewMode === "favorites" ? (
              <>
                <Heart className="w-4 h-4" />
                Favorites
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                Results
              </>
            )}
          </h3>
          <span className="search-results__count">
            {countLabel}
          </span>
        </div>
        
        <div className="search-results__header-actions">
          <input
            type="text"
            value={nameFilter}
            onChange={(event) => setNameFilter(event.target.value)}
            placeholder="Filter by name"
            className="form-control search-results__name-filter"
            aria-label="Filter loaded results by product name"
          />

          {/* Export button - always visible, disabled when searching or no favorites */}
          <button
            onClick={handleExportFavorites}
            disabled={isExporting || isLoading || favorites.length === 0}
            className="search-results__export-btn"
            aria-label="Export favorites"
            title={
              favorites.length === 0 
                ? "No favorites to export" 
                : isLoading 
                ? "Cannot export while searching"
                : isExporting
                ? (exportProgress ? `${exportProgress.message} (${exportProgress.current}/${exportProgress.total})` : "Exporting...")
                : "Export favorites as ZIP"
            }
          >
            <Download className="w-4 h-4" />
            {isExporting ? (exportProgress ? `${Math.round((exportProgress.current / exportProgress.total) * 100)}%` : "Exporting...") : "Export"}
          </button>
          
          <div className="search-results__view-controls">
            <button
              onClick={() => setViewMode("grid")}
              disabled={isLoading}
              className={`search-results__view-btn ${
                viewMode === "grid" ? "search-results__view-btn--active" : ""
              }`}
              aria-label="Grid view"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("favorites")}
              disabled={isLoading}
              className={`search-results__view-btn ${
                viewMode === "favorites" ? "search-results__view-btn--active" : ""
              }`}
              aria-label="Favorites view"
            >
              <Heart className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Results content */}
      <div className="search-results__content">
        {filteredDisplayProducts.length === 0 ? (
          <div className="search-results__empty">
            <Package className="w-12 h-12 text-gray-400" />
            <h3>No matching products</h3>
            <p>Try a looser name filter or clear the field.</p>
          </div>
        ) : (
        <div className="search-results__grid">
          {filteredDisplayProducts.map((product) => {
            return (
            <div 
              key={product.id} 
              className="search-result-card"
              onClick={() => {
                handleProductClick(product.id);
              }}
            >
              <div className="search-result-card__image">
                <ImageWithPlaceholder
                  src={product.image}
                  alt={getProductNameText(product)}
                  fill
                  className="search-result-card__img"
                  sizes="200px"
                  unoptimized
                />
                <button
                  className={`search-result-card__favorite ${
                    isFavorited(product.id) ? "search-result-card__favorite--active" : ""
                  }`}
                  onClick={(e) => handleFavoriteClick(e, product)}
                  aria-label={isFavorited(product.id) ? "Remove from favorites" : "Add to favorites"}
                >
                  <Heart 
                    className="w-4 h-4" 
                    fill={isFavorited(product.id) ? "currentColor" : "none"}
                  />
                </button>
              </div>
              
              <div className="search-result-card__content">
                <div className="search-result-card__info">
                  <div className={`search-result-card__similarity ${getSimilarityColorClass(getSimilarity(product))}`}>
                    {getSimilarity(product)}%
                  </div>
                  <h3 className="search-result-card__title">
                    {formatProductName(product)}
                  </h3>
                </div>
              </div>
            </div>
            );
          })}
        </div>
        )}
      </div>
    </div>
  );
}