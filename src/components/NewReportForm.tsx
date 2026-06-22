'use client';

import { useMemo, useRef, useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { FileText } from 'lucide-react';
import type { FormEvent } from 'react';

type FlooringOption = {
  value: string;
  materials: string[];
};

type NewReportFormProps = {
  // onSubmit now receives the form state plus an `author` string (user id)
  onSubmit?: (data: NewReportFormState & { author: string }) => void;
  onDimensionsChange?: (enabled: boolean) => void;
  onDimensionsValues?: (vals: { length: number | null; width: number | null; thickness: number | null }) => void;
  imageCount?: number;
  // Expose ref to complete progress when API call finishes
  onProgressComplete?: (completeFunction: () => void) => void;
  // Callback to notify parent about submission state
  onSubmissionStateChange?: (isSubmitting: boolean) => void;
};

type NewReportFormState = {
  reportName: string;
  flooringType: string;
  material: string;
  look: string;
  texture: string;
  finish: string;
  edge: string;
  length: string;
  width: string;
  thickness: string;
  units: 'relative' | 'absolute';
};

const FLOORING_OPTIONS: FlooringOption[] = [
  { value: 'Any', materials: [] },
  { value: 'Tile', materials: ['Ceramic', 'Porcelain', 'Stone', 'Mosaic'] },
  { value: 'Wood', materials: ['Oak', 'Maple', 'Walnut', 'Bamboo'] },
  { value: 'Vinyl', materials: ['Luxury Vinyl', 'Sheet Vinyl', 'Rigid Core'] },
  { value: 'Laminate', materials: ['High Gloss', 'Textured', 'Water Resistant'] },
  { value: 'Carpet', materials: ['Nylon', 'Polyester', 'Wool'] },
];

const INITIAL_FORM_STATE: NewReportFormState = {
  reportName: '',
  flooringType: 'Any',
  material: 'Any',
  look: 'Any',
  texture: 'Any',
  finish: 'Any',
  edge: 'Any',
  length: '',
  width: '',
  thickness: '',
  units: 'absolute',
};

const INITIAL_TOUCHED_STATE = {
  reportName: false,
};

export function NewReportForm({ onSubmit, onDimensionsChange, onDimensionsValues, imageCount = 0, onProgressComplete, onSubmissionStateChange }: NewReportFormProps) {
  const [form, setForm] = useState<NewReportFormState>(INITIAL_FORM_STATE);
  const { user } = useAuth();
  const [touched, setTouched] = useState(INITIAL_TOUCHED_STATE);
  const [isReportNameFocused, setIsReportNameFocused] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const reportNameRef = useRef<HTMLInputElement>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const selectedFlooring = useMemo(
    () => FLOORING_OPTIONS.find((option) => option.value === form.flooringType),
    [form.flooringType]
  );

  const materialOptions = useMemo(() => {
    if (!selectedFlooring || selectedFlooring.materials.length === 0) {
      return [] as string[];
    }

    return selectedFlooring.materials;
  }, [selectedFlooring]);

  const handleFlooringChange = (value: string) => {
    setForm((prev) => ({
      ...prev,
      flooringType: value,
      material: 'Any',
    }));
  };

  const handleMaterialChange = (value: string) => {
    setForm((prev) => ({
      ...prev,
      material: value,
    }));
  };

  const NUMERIC_RE = /^\d*(?:\.\d*)?$/;

  const handleNumericChange = (field: 'length' | 'width' | 'thickness', value: string) => {
    // allow empty string
    if (value === '') {
      setForm((prev) => ({ ...prev, [field]: '' }));
      return;
    }

    // reject negative sign or multiple decimals; allow digits and single optional decimal
    if (!NUMERIC_RE.test(value)) return;

    setForm((prev) => ({ ...prev, [field]: value }));
  };

  // Notify parent about whether both length and width are present — run in effect to avoid
  // calling parent's setState during render of this component.
  useEffect(() => {
    try {
      onDimensionsChange?.(form.length !== '' && form.width !== '');
      const lengthVal = form.length === '' ? null : Number.parseFloat(form.length);
      const widthVal = form.width === '' ? null : Number.parseFloat(form.width);
      const thicknessVal = form.thickness === '' ? null : Number.parseFloat(form.thickness);
      onDimensionsValues?.({ length: lengthVal, width: widthVal, thickness: thicknessVal });
    } catch {
      // ignore
    }
  }, [form.length, form.width, form.thickness, onDimensionsChange, onDimensionsValues]);

  // Clear error message when images are added
  useEffect(() => {
    if ((imageCount ?? 0) > 0) {
      if (errorMessage && errorMessage.includes('Please add at least one image')) {
        setErrorMessage(null);
      }
    }
  }, [imageCount, errorMessage]);

  // Cleanup progress interval on unmount
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
    };
  }, []);

  // Function to complete progress when API call finishes (to be called from parent)
  const completeProgress = useCallback(() => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
    // Quickly complete to 100%
    setProgress(100);
    // Hide overlay after brief completion animation
    setTimeout(() => {
      setIsSubmitting(false);
      setProgress(0);
    }, 500);
  }, []);

  // Provide the completion function to parent
  useEffect(() => {
    onProgressComplete?.(completeProgress);
  }, [onProgressComplete, completeProgress]);

  // Notify parent of submission state changes
  useEffect(() => {
    onSubmissionStateChange?.(isSubmitting);
  }, [isSubmitting, onSubmissionStateChange]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (form.reportName.trim() === '') {
      setTouched((prev) => ({ ...prev, reportName: true }));
      setIsReportNameFocused(false);
      return;
    }

    // Check dimensions when relative is selected
    if (form.units === 'relative' && (form.length.trim() === '' || form.width.trim() === '')) {
      return;
    }

    if ((imageCount ?? 0) === 0) {
      setErrorMessage('Please add at least one image before creating a report.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setProgress(0);
    
    // Start progress bar animation (30-40 second duration)
    const totalDuration = 35000; // 35 seconds
    const intervalMs = 100; // Update every 100ms
    const increment = 100 / (totalDuration / intervalMs);
    
    progressIntervalRef.current = setInterval(() => {
      setProgress(prev => {
        const next = prev + increment;
        // Slow down as it approaches 90% to leave buffer for completion
        if (next >= 90) {
          return Math.min(90, prev + increment * 0.1); // Slow down significantly
        }
        return next;
      });
    }, intervalMs);
    
    try {
      // attach author from current auth state if available
      const author = user?.id ?? 'guest';
      onSubmit?.({ ...form, author });
    } catch {
      setErrorMessage('Failed to create report. Please try again.');
      // Clean up progress on error
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
      setIsSubmitting(false);
      setProgress(0);
    }
  };

  const handleReportNameFocus = () => {
    setIsReportNameFocused(true);
  };

  const handleReportNameBlur = () => {
    setIsReportNameFocused(false);
    setTouched((prev) => ({ ...prev, reportName: true }));
  };

  const isReportNameMissing =
    touched.reportName && !isReportNameFocused && form.reportName.trim() === '';
  const reportNameErrorId = isReportNameMissing ? 'report-name-error' : undefined;

  // Validation for dimensions when relative is selected
  const areDimensionsMissing = 
    form.units === 'relative' && 
    (form.length.trim() === '' || form.width.trim() === '');
  const dimensionsErrorId = areDimensionsMissing ? 'dimensions-error' : undefined;

  // Determine whether submit button should be enabled: needs report name and at least one image
  // Also needs length and width when relative is selected
  const canSubmit = form.reportName.trim() !== '' && 
    (imageCount ?? 0) > 0 && 
    (form.units === 'absolute' || (form.length.trim() !== '' && form.width.trim() !== ''));

  return (
    <div className="search-filters">
      <div className="search-filters__header search-filters__header--strip-top">
        <h3 className="search-filters__title">
          <FileText className="w-4 h-4" />
          New Report
        </h3>
      </div>

      <div className="search-filters__content">
          <div className="search-filters__section">
            <h4 className="search-filters__section-title">Report Name <span className="form-field__required-asterisk">*</span></h4>
            <div className="search-filters__field search-filters__field--vertical">
              <input
                id="report-name"
                ref={reportNameRef}
                value={form.reportName}
                onChange={(event) => {
                  const value = event.target.value;
                  setForm((prev) => ({
                    ...prev,
                    reportName: value,
                  }));
                  setTouched((prev) => ({ ...prev, reportName: false }));
                }}
                placeholder="Enter report name"
                onFocus={handleReportNameFocus}
                onBlur={handleReportNameBlur}
                aria-invalid={isReportNameMissing}
                aria-describedby={reportNameErrorId}
                className={`form-control${isReportNameMissing ? ' form-control--error' : ''}`}
              />
              {isReportNameMissing && (
                <p className="form-field__hint" id={reportNameErrorId} role="alert">
                  Please enter a report name.
                </p>
              )}
            </div>
          </div>

          <div className="search-filters__section">
            <h4 className="search-filters__section-title">Category</h4>
            <div className="search-filters__field">
              <label htmlFor="flooring-type" className="search-filters__label">
                Type
              </label>
              <select
                id="flooring-type"
                value={form.flooringType}
                onChange={(event) => handleFlooringChange(event.target.value)}
                className="form-control select-control"
              >
                {FLOORING_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.value}
                  </option>
                ))}
              </select>
            </div>

            <div className="search-filters__field">
              <label htmlFor="flooring-material" className="search-filters__label">
                Material
              </label>
              <select
                id="flooring-material"
                value={form.material}
                onChange={(event) => handleMaterialChange(event.target.value)}
                className="form-control select-control"
              >
                <option value="Any">Any</option>
                {materialOptions.map((material) => (
                  <option key={material} value={material}>
                    {material}
                  </option>
                ))}
              </select>
            </div>

            <div className="search-filters__field">
              <label htmlFor="look" className="search-filters__label">
                Look
              </label>
              <select
                id="look"
                value={form.look}
                onChange={(e) => setForm((prev) => ({ ...prev, look: e.target.value }))}
                className="form-control select-control"
              >
                <option value="Any">Any</option>
                <option value="antiqued">Antiqued</option>
                <option value="rustic">Rustic</option>
              </select>
            </div>

            <div className="search-filters__field">
              <label htmlFor="texture" className="search-filters__label">
                Texture
              </label>
              <select
                id="texture"
                value={form.texture}
                onChange={(e) => setForm((prev) => ({ ...prev, texture: e.target.value }))}
                className="form-control select-control"
              >
                <option value="Any">Any</option>
                <option value="hand-scraped">Hand-scraped</option>
                <option value="sanded">Sanded</option>
                <option value="textured">Textured</option>
              </select>
            </div>

            <div className="search-filters__field">
              <label htmlFor="finish" className="search-filters__label">
                Finish
              </label>
              <select
                id="finish"
                value={form.finish}
                onChange={(e) => setForm((prev) => ({ ...prev, finish: e.target.value }))}
                className="form-control select-control"
              >
                <option value="Any">Any</option>
                <option value="glossy">Glossy</option>
                <option value="honed">Honed</option>
                <option value="matte">Matte</option>
                <option value="natural">Natural</option>
                <option value="polished">Polished</option>
                <option value="satin">Satin</option>
              </select>
            </div>

            <div className="search-filters__field">
              <label htmlFor="edge" className="search-filters__label">
                Edge
              </label>
              <select
                id="edge"
                value={form.edge}
                onChange={(e) => setForm((prev) => ({ ...prev, edge: e.target.value }))}
                className="form-control select-control"
              >
                <option value="Any">Any</option>
                <option value="beveled">Beveled</option>
                <option value="chiseled">Chiseled</option>
                <option value="rectified">Rectified</option>
              </select>
            </div>
          </div>

          <div className="search-filters__section">
            <h4 className="search-filters__section-title">Dimensions</h4>
            <div className="search-filters__field">
              <label htmlFor="length" className="search-filters__label">
                Length{form.units === 'absolute' ? ' (in)' : ''}{form.units === 'relative' && <span className="form-field__required-asterisk"> *</span>}
              </label>
              <input
                id="length"
                type="text"
                inputMode="decimal"
                pattern="^\d*(?:\.\d*)?$"
                value={form.length}
                onChange={(event) => handleNumericChange('length', event.target.value)}
                aria-invalid={form.units === 'relative' && form.length.trim() === ''}
                aria-describedby={dimensionsErrorId}
                className={`form-control${form.units === 'relative' && form.length.trim() === '' ? ' form-control--error' : ''}`}
              />
            </div>
            <div className="search-filters__field">
              <label htmlFor="width" className="search-filters__label">
                Width{form.units === 'absolute' ? ' (in)' : ''}{form.units === 'relative' && <span className="form-field__required-asterisk"> *</span>}
              </label>
              <input
                id="width"
                type="text"
                inputMode="decimal"
                pattern="^\d*(?:\.\d*)?$"
                value={form.width}
                onChange={(event) => handleNumericChange('width', event.target.value)}
                aria-invalid={form.units === 'relative' && form.width.trim() === ''}
                aria-describedby={dimensionsErrorId}
                className={`form-control${form.units === 'relative' && form.width.trim() === '' ? ' form-control--error' : ''}`}
              />
            </div>
            {areDimensionsMissing && (
              <div className="search-filters__field search-filters__field--vertical">
                <p className="form-field__hint" id={dimensionsErrorId} role="alert">
                  Both length and width are required when using relative units.
                </p>
              </div>
            )}
            <div className="search-filters__field">
              <label htmlFor="thickness" className="search-filters__label">
                Depth (mm)
              </label>
              <input
                id="thickness"
                type="text"
                inputMode="decimal"
                pattern="^\d*(?:\.\d*)?$"
                value={form.thickness}
                onChange={(event) => handleNumericChange('thickness', event.target.value)}
                className="form-control"
              />
            </div>
            <div
              className="form-field form-field--inline"
              role="radiogroup"
              aria-labelledby="units-label"
            >
              <span
                id="units-label"
                className="form-field__label form-field__label--secondary"
              >
                Units
              </span>
              <div className="form-radio-group">
                <label className="form-radio">
                  <input
                    type="radio"
                    name="units"
                    value="absolute"
                    checked={form.units === 'absolute'}
                    onChange={() =>
                      setForm((prev) => ({
                        ...prev,
                        units: 'absolute',
                      }))
                    }
                  />
                  <span>Absolute</span>
                </label>
                <label className="form-radio">
                  <input
                    type="radio"
                    name="units"
                    value="relative"
                    checked={form.units === 'relative'}
                    onChange={() =>
                      setForm((prev) => ({
                        ...prev,
                        units: 'relative',
                      }))
                    }
                  />
                  <span>Relative</span>
                </label>
              </div>
            </div>
          </div>

          <div className="search-filters__section">
            <h4 className="search-filters__section-title">Reference Images <span className="form-field__required-asterisk">*</span></h4>
            <div className="search-filters__field search-filters__field--vertical">
              {(imageCount ?? 0) === 0 && (
                <p className="form-field__hint">
                  Add images using the workspace on the right. At least one image is required.
                </p>
              )}
              {imageCount > 0 && (
                <p className="form-field__hint" style={{ color: 'var(--text-subtle)' }}>
                  {imageCount} image{imageCount !== 1 ? 's' : ''} added
                </p>
              )}
            </div>
          </div>

          {/* Error message within scrollable content */}
          {errorMessage && (
            <div className="form-field__hint" role="alert">
              {errorMessage}
            </div>
          )}
      </div>

      {/* Sticky footer with submit button */}
      <div className="search-filters__footer">
        <form id="report-form" onSubmit={handleSubmit}>
        <button
          type="submit"
          className="button button--primary search-filters__search-btn"
          disabled={!canSubmit || isSubmitting}
          aria-disabled={!canSubmit || isSubmitting}
        >
          {isSubmitting ? (
            <svg className="button-spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
              <circle cx="12" cy="12" r="10" stroke="#ffffff33" strokeWidth="4" />
              <path d="M22 12A10 10 0 0 1 12 22" stroke="#ffffff" strokeWidth="4" strokeLinecap="round" />
            </svg>
          ) : (
            'Create Report'
          )}
        </button>
        </form>
      </div>

      {/* Loading Overlay */}
      {isSubmitting && (
        <div className="report-creation-overlay">
          <div className="report-creation-modal">
            <div className="report-creation-content">
              <div className="report-creation-icon">
                <FileText size={48} />
              </div>
              <h3 className="report-creation-title">Creating Your Report</h3>
              <p className="report-creation-message">
                We&apos;re analyzing your images and preparing your material matches. This may take up to 30 seconds.
              </p>
              
              {/* Progress Bar */}
              <div className="progress-container">
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <div className="progress-text">
                  {Math.round(progress)}%
                </div>
              </div>
              
              <p className="report-creation-subtitle">
                Please don&apos;t close this window or navigate away.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export type { NewReportFormState };
