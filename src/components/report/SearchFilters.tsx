"use client";

import { useMemo, useState } from "react";
import { Search, Sliders } from "lucide-react";
import type { Product } from "@/types/report";

export interface SearchFilters {
  maxLengthDiff?: number;
  maxWidthDiff?: number;
  maxThicknessDiff?: number;
  aspectRatioTolerance?: number;
  selectMode: 'color' | 'pattern';
  brand?: string[];
  categories: {
    type?: string[];
    material?: string[];
    look?: string[];
    texture?: string[];
    finish?: string[];
    edge?: string[];
  };
}

const KEYWORD_FILTER_OPTIONS = {
  look: ['antiqued', 'rustic'],
  texture: ['hand-scraped', 'sanded', 'textured'],
  finish: ['glossy', 'honed', 'matte', 'natural', 'polished', 'satin'],
  edge: ['beveled', 'chiseled', 'rectified'],
} as const;

const keywordFilterLabels: Record<keyof typeof KEYWORD_FILTER_OPTIONS, string> = {
  look: 'Look',
  texture: 'Texture',
  finish: 'Finish',
  edge: 'Edge',
};

const BRAND_FILTER_OPTIONS = [
  'American Olean',
  'D&B Tile',
  'Floor & Decor',
  'Happy Floors',
  'Home Depot',
  'Merola Tile',
  'NHD Tile',
  'Shaw Floors',
  'Stone & Tile Shoppe',
  'USTiles',
] as const;

function formatKeywordDisplay(value: string): string {
  return value
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join('-');
}

function normalizeKeywordValue(value?: string): string | undefined {
  const normalized = value?.trim().toLowerCase();
  return normalized ? normalized : undefined;
}

interface SearchFiltersProps {
  referenceProduct: Product;
  onSearch: (filters: SearchFilters) => void;
  isSearching: boolean;
  filters?: SearchFilters | null;
  onFiltersChange?: (filters: SearchFilters) => void;
}

export function SearchFilters({ referenceProduct, onSearch, isSearching, filters: externalFilters, onFiltersChange }: SearchFiltersProps) {
  const format = referenceProduct.formats?.[0];
  const hasAbsoluteDimensions = format?.length?.unit !== 'none' && format?.width?.unit !== 'none';

  const keywordFilterOptions = useMemo(() => {
    const merged = {
      look: [...KEYWORD_FILTER_OPTIONS.look],
      texture: [...KEYWORD_FILTER_OPTIONS.texture],
      finish: [...KEYWORD_FILTER_OPTIONS.finish],
      edge: [...KEYWORD_FILTER_OPTIONS.edge],
    };

    const referenceLook = normalizeKeywordValue(referenceProduct.category.look);
    const referenceTexture = normalizeKeywordValue(referenceProduct.category.texture);
    const referenceFinish = normalizeKeywordValue(referenceProduct.category.finish);
    const referenceEdge = normalizeKeywordValue(referenceProduct.category.edge);

    if (referenceLook && !merged.look.includes(referenceLook)) {
      merged.look.push(referenceLook);
    }
    if (referenceTexture && !merged.texture.includes(referenceTexture)) {
      merged.texture.push(referenceTexture);
    }
    if (referenceFinish && !merged.finish.includes(referenceFinish)) {
      merged.finish.push(referenceFinish);
    }
    if (referenceEdge && !merged.edge.includes(referenceEdge)) {
      merged.edge.push(referenceEdge);
    }

    return merged;
  }, [referenceProduct.category.edge, referenceProduct.category.finish, referenceProduct.category.look, referenceProduct.category.texture]);
  
  // Determine which filters to show
  const hasLength = format?.length?.val;
  const hasWidth = format?.width?.val;
  const hasThickness = format?.thickness?.val;
  const isRelative = format?.length?.unit === 'none' || format?.width?.unit === 'none';
  
  // Aspect ratio filter only makes sense for relative dimensions (where we have an actual ratio)
  const showAspectRatioFilter = isRelative && hasLength && hasWidth;
  
  // Calculate reference aspect ratio for display
  const referenceAspectRatio = (() => {
    if (hasLength && hasWidth && format?.length?.val && format?.width?.val) {
      const ratio = format.length.val / format.width.val;
      return ratio;
    }
    return null;
  })();
  
  // Default filter values
  const getDefaultFilters = (): SearchFilters => ({
    maxLengthDiff: 1,
    maxWidthDiff: 1,
    // Only include thickness default if reference product has thickness
    maxThicknessDiff: hasThickness ? 1 : undefined,
    aspectRatioTolerance: 2,
    selectMode: 'color',
    brand: [],
    categories: {
      // Pre-populate with reference product categories for convenience
      type: referenceProduct.category.type ? [referenceProduct.category.type] : [],
      material: referenceProduct.category.material ? [referenceProduct.category.material] : [],
      look: normalizeKeywordValue(referenceProduct.category.look) ? [normalizeKeywordValue(referenceProduct.category.look)!] : [],
      texture: normalizeKeywordValue(referenceProduct.category.texture) ? [normalizeKeywordValue(referenceProduct.category.texture)!] : [],
      finish: normalizeKeywordValue(referenceProduct.category.finish) ? [normalizeKeywordValue(referenceProduct.category.finish)!] : [],
      edge: normalizeKeywordValue(referenceProduct.category.edge) ? [normalizeKeywordValue(referenceProduct.category.edge)!] : [],
    }
  });

  // Use external filters if provided, otherwise use local state
  const [localFilters, setLocalFilters] = useState<SearchFilters>(getDefaultFilters);
  const filters = externalFilters || localFilters;
  
  // Calculate tolerance range for display
  const getToleranceRange = () => {
    if (referenceAspectRatio) {
      // Use 0 as default tolerance when input is empty/undefined
      const tolerance = (filters.aspectRatioTolerance ?? 0) / 100;
      const minRatio = referenceAspectRatio * (1 - tolerance);
      const maxRatio = referenceAspectRatio * (1 + tolerance);
      return {
        min: minRatio.toFixed(2),
        max: maxRatio.toFixed(2),
        reference: referenceAspectRatio.toFixed(2),
        tolerancePercent: filters.aspectRatioTolerance ?? 0
      };
    }
    return null;
  };

  const handleFilterChange = (key: keyof SearchFilters, value: unknown) => {
    const newFilters = {
      ...filters,
      [key]: value
    };
    
    if (onFiltersChange) {
      onFiltersChange(newFilters);
    } else {
      setLocalFilters(newFilters);
    }
  };

  const handleSearch = () => {
    onSearch(filters);
  };

  const toggleKeywordValue = (
    field: keyof Pick<SearchFilters['categories'], 'look' | 'texture' | 'finish' | 'edge'>,
    value: string
  ) => {
    const currentValues = filters.categories[field] || [];
    const nextValues = currentValues.includes(value)
      ? currentValues.filter((item) => item !== value)
      : [...currentValues, value];

    handleFilterChange('categories', {
      ...filters.categories,
      [field]: nextValues,
    });
  };

  const toggleBrandValue = (value: string) => {
    const currentValues = filters.brand || [];
    const nextValues = currentValues.includes(value)
      ? currentValues.filter((item) => item !== value)
      : [...currentValues, value];

    handleFilterChange('brand', nextValues);
  };

  const resetFilters = () => {
    const defaultFilters = getDefaultFilters();
    
    if (onFiltersChange) {
      onFiltersChange(defaultFilters);
    } else {
      setLocalFilters(defaultFilters);
    }
  };

  return (
    <div className="search-filters">
      <div className="search-filters__header">
        <h3 className="search-filters__title">
          <Sliders className="w-4 h-4" />
          Filters
        </h3>
        <button 
          onClick={resetFilters}
          className="search-filters__reset"
        >
          Reset
        </button>
      </div>

            <div className="search-filters__content">
        {/* Dimension Filters - conditional based on available dimensions */}
        <div className="search-filters__section">
          <h4 className="search-filters__section-title">Dimension Similarity</h4>
          
          {/* Show aspect ratio filter only for relative dimensions with both length and width */}
          {showAspectRatioFilter && (
            <div className="search-filters__field">
              <div className="search-filters__label-container">
                <label className="search-filters__label">
                  Aspect Ratio Tolerance (%)
                </label>
                {(() => {
                  const range = getToleranceRange();
                  return range ? (
                    <div className="search-filters__reference-note">
                      {range.reference} ± {range.tolerancePercent}% ({range.min} - {range.max})
                    </div>
                  ) : null;
                })()}
              </div>
              <input
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={filters.aspectRatioTolerance ?? ''}
                onKeyDown={(e) => {
                  // Allow: backspace, delete, tab, escape, enter, period
                  if ([8, 9, 27, 13, 46, 110, 190].indexOf(e.keyCode) !== -1 ||
                      // Allow: Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
                      (e.keyCode === 65 && e.ctrlKey === true) ||
                      (e.keyCode === 67 && e.ctrlKey === true) ||
                      (e.keyCode === 86 && e.ctrlKey === true) ||
                      (e.keyCode === 88 && e.ctrlKey === true) ||
                      // Allow: home, end, left, right
                      (e.keyCode >= 35 && e.keyCode <= 39)) {
                    return;
                  }
                  // Ensure that it is a number and stop the keypress
                  if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
                    e.preventDefault();
                  }
                }}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === '') {
                    // Allow empty value during typing
                    handleFilterChange('aspectRatioTolerance', undefined);
                  } else {
                    const numValue = parseFloat(value);
                    if (!isNaN(numValue) && numValue >= 0 && numValue <= 100) {
                      handleFilterChange('aspectRatioTolerance', numValue);
                    }
                  }
                }}
                onBlur={(e) => {
                  // Set default value on blur if empty
                  if (e.target.value === '' || filters.aspectRatioTolerance === undefined) {
                    handleFilterChange('aspectRatioTolerance', 2);
                  }
                }}
                className="form-control"
              />
            </div>
          )}
          
          {/* Show length filter for absolute dimensions when length is set */}
          {hasAbsoluteDimensions && hasLength && (
            <div className="search-filters__field">
              <label className="search-filters__label">
                Δ Length ({format?.length?.unit || 'in'})
              </label>
              <input
                type="number"
                min="0"
                max="10"
                step="0.5"
                value={filters.maxLengthDiff || ''}
                onChange={(e) => {
                  const value = e.target.value === '' ? 0 : parseFloat(e.target.value);
                  if (!isNaN(value) && value >= 0 && value <= 10) {
                    handleFilterChange('maxLengthDiff', value);
                  }
                }}
                className="form-control"
                placeholder="1.0"
              />
            </div>
          )}

          {/* Show width filter for absolute dimensions when width is set */}
          {hasAbsoluteDimensions && hasWidth && (
            <div className="search-filters__field">
              <label className="search-filters__label">
                Δ Width ({format?.width?.unit || 'in'})
              </label>
              <input
                type="number"
                min="0"
                max="10"
                step="0.5"
                value={filters.maxWidthDiff || ''}
                onChange={(e) => {
                  const value = e.target.value === '' ? 0 : parseFloat(e.target.value);
                  if (!isNaN(value) && value >= 0 && value <= 10) {
                    handleFilterChange('maxWidthDiff', value);
                  }
                }}
                className="form-control"
                placeholder="1.0"
              />
            </div>
          )}

          {/* Show thickness filter only if thickness is set */}
          {hasThickness && (
            <div className="search-filters__field">
              <label className="search-filters__label">
                Δ Depth (mm)
              </label>
              <input
                type="number"
                min="0"
                max="20"
                step="0.5"
                value={filters.maxThicknessDiff || ''}
                onChange={(e) => {
                  const value = e.target.value === '' ? 0 : parseFloat(e.target.value);
                  if (!isNaN(value) && value >= 0 && value <= 20) {
                    handleFilterChange('maxThicknessDiff', value);
                  }
                }}
                className="form-control"
                placeholder="1.0"
              />
            </div>
          )}
        </div>

        {/* Image Similarity */}
        <div className="search-filters__section">
          <h4 className="search-filters__section-title">Image Similarity</h4>

          <div className="search-filters__field search-filters__field--vertical">
            <label className="search-filters__label">Select Mode</label>
            <div className="checkbox-group">
              <label className="checkbox-label">
                <input
                  type="radio"
                  name="image-similarity-mode"
                  checked={filters.selectMode === 'color'}
                  onChange={() => handleFilterChange('selectMode', 'color')}
                  className="checkbox-input"
                />
                <span className="checkbox-custom"></span>
                Color
              </label>
              <label className="checkbox-label">
                <input
                  type="radio"
                  name="image-similarity-mode"
                  checked={filters.selectMode === 'pattern'}
                  onChange={() => handleFilterChange('selectMode', 'pattern')}
                  className="checkbox-input"
                />
                <span className="checkbox-custom"></span>
                Pattern
              </label>
            </div>
          </div>
        </div>

        <div className="search-filters__section">
          <h4 className="search-filters__section-title">Keywords</h4>
          {(Object.keys(keywordFilterOptions) as Array<keyof typeof keywordFilterOptions>).map((field) => (
            <div key={field} className="search-filters__field search-filters__field--vertical">
              <label className="search-filters__label">{keywordFilterLabels[field]}</label>
              <div className="checkbox-group">
                {keywordFilterOptions[field].map((value) => {
                  const checked = (filters.categories[field] || []).includes(value);
                  return (
                    <label key={value} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleKeywordValue(field, value)}
                        className="checkbox-input"
                      />
                      <span className="checkbox-custom"></span>
                      {formatKeywordDisplay(value)}
                    </label>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="search-filters__section">
          <h4 className="search-filters__section-title">Branding</h4>
          <div className="search-filters__field search-filters__field--vertical">
            <label className="search-filters__label">Store</label>
            <div className="checkbox-group">
              {BRAND_FILTER_OPTIONS.map((value) => {
                const checked = (filters.brand || []).includes(value);
                return (
                  <label key={value} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleBrandValue(value)}
                      className="checkbox-input"
                    />
                    <span className="checkbox-custom"></span>
                    {value}
                  </label>
                );
              })}
            </div>
          </div>
        </div>

      </div>

      {/* Search Button */}
      <div className="search-filters__footer">
        <button
          onClick={handleSearch}
          disabled={isSearching}
          className="button button--primary search-filters__search-btn"
        >
          <Search className="w-4 h-4" />
          {isSearching ? "Searching..." : "Search Similar Products"}
        </button>
      </div>
    </div>
  );
}