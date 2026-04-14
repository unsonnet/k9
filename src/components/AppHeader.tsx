"use client";

import { useAuth } from "@/hooks/useAuth";
import { decodeReportId } from "@/lib/utils/jobIdentifiers";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useState, useEffect, useRef } from "react";

export function AppHeader() {
  const { user, loading, signOut } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [reportTitle, setReportTitle] = useState<string | null>(null);
  const [productTitle, setProductTitle] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Track hydration to ensure consistent rendering
  useEffect(() => {
    setMounted(true);
  }, []);

  // Handle clicking outside to close menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [showUserMenu]);

  // Fetch report title when on fetch page
  useEffect(() => {
    if (pathname.startsWith('/fetch')) {
      // Get report ID from search params
      const reportParam = searchParams.get('report');
      const idParam = searchParams.get('id');
      const productParam = searchParams.get('product');
      
      // Use report param first, then id param as fallback
      const reportId = reportParam || idParam;
      
      if (reportId) {
        setReportTitle(decodeReportId(reportId));
        
        // For product comparison, just use the product ID as title for now
        // The actual product name will be loaded by the main component
        if (productParam) {
          setProductTitle(productParam);
        } else {
          setProductTitle(null);
        }
      } else {
        setReportTitle(null);
        setProductTitle(null);
      }
    } else {
      setReportTitle(null);
      setProductTitle(null);
    }
  }, [pathname, searchParams]);

  const shouldShowBackButton = () => {
    const shouldShow = pathname !== '/dashboard' && pathname !== '/dashboard/' && pathname !== '/';
    return shouldShow;
  };

  const handleBackClick = () => {
    if (pathname === '/create') {
      router.push('/dashboard');
    } else if (pathname.startsWith('/fetch')) {
      const productParam = searchParams.get('product');
      const reportParam = searchParams.get('report');
      
      if (productParam && reportParam) {
        // In product comparison view, go back to report by removing product parameter
        const backUrl = `/fetch?report=${reportParam}`;
        router.push(backUrl);
      } else {
        // Regular report page, go back to dashboard
        // Clear session storage for this report when leaving fetch page
        if (reportParam && typeof window !== 'undefined') {
          try {
            sessionStorage.removeItem(`report_filters_${reportParam}`);
            sessionStorage.removeItem(`report_results_${reportParam}`);
            sessionStorage.removeItem(`report_searched_${reportParam}`);
          } catch (error) {
            console.warn('Failed to clear report session data:', error);
          }
        }
        router.push('/dashboard');
      }
    } else {
      router.back();
    }
  };

  const getPageTitle = () => {
    if (pathname === '/dashboard' || pathname === '/dashboard/' || pathname === '/') {
      return 'Dashboard';
    }
    if (pathname === '/create' || pathname === '/create/') {
      return 'Create';
    }
    if (pathname.startsWith('/fetch')) {
      const productParam = searchParams.get('product');
      if (productParam) {
        return productTitle ? (
          <>
            <span>Compare:</span>
            <span className="app-header-universal__subtitle">{productTitle}</span>
          </>
        ) : 'Compare';
      }
      return reportTitle ? (
        <>
          <span>Fetch:</span>
          <span className="app-header-universal__subtitle">{reportTitle}</span>
        </>
      ) : 'Fetch';
    }
    if (pathname.startsWith('/edit')) return 'Edit Search';
    
    return 'K9 Search';
  };

  return (
    <header className="app-header-universal">
      <div className="app-header-universal__left">
        {shouldShowBackButton() ? (
          <button
            onClick={handleBackClick}
            className="app-header-universal__back-btn"
            title="Go back"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 12H5M12 19L5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        ) : (
          <div className="app-header-universal__back-btn-spacer" />
        )}
        
        <div className="app-header-universal__logo">
          <div className="app-header-universal__logo-icon">
            {/* Company logo placeholder - replace with actual logo */}
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
              <path d="M9 9h6v6H9z" fill="currentColor"/>
            </svg>
          </div>
          <h1 className="app-header-universal__title">{getPageTitle()}</h1>
        </div>
      </div>

      <div className="app-header-universal__right">
        {!mounted || loading ? (
          <div className="app-header-universal__user">
            <span className="app-header-universal__username">Loading...</span>
            <div className="app-header-universal__avatar skeleton" />
          </div>
        ) : user ? (
          <div className="app-header-universal__user">
            <div className="app-header-universal__user-menu" ref={userMenuRef}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="app-header-universal__user-button"
                title="User menu"
              >
                <span className="app-header-universal__username">{user.name}</span>
                <div className="app-header-universal__avatar">
                  {user.name.charAt(0).toUpperCase()}
                </div>
              </button>
              
              {showUserMenu && (
                <div className="app-header-universal__user-menu-dropdown">
                  <div className="app-header-universal__user-info">
                    <strong>{user.name}</strong>
                    <span>{user.email || 'No email'}</span>
                  </div>
                  <hr className="app-header-universal__user-menu-divider" />
                  <button
                    disabled
                    onClick={() => {
                      // TODO: Navigate to settings
                      setShowUserMenu(false);
                    }}
                    className="app-header-universal__user-menu-item"
                    title="Settings (Coming Soon)"
                  >
                    Settings
                  </button>
                  <button
                    onClick={() => {
                      signOut();
                      setShowUserMenu(false);
                    }}
                    className="app-header-universal__user-menu-item app-header-universal__user-menu-item--danger"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="app-header-universal__user">
            <button
              onClick={() => router.push('/')}
              className="app-header-universal__login-btn"
              title="Log in"
            >
              Log In
            </button>
          </div>
        )}
        {/* Right spacer for symmetry */}
        <div className="app-header-universal__right-spacer" />
      </div>
    </header>
  );
}