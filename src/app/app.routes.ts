import { Routes } from '@angular/router';
import { SearchPage } from './pages/search/search.page';
import { ResultsPage } from './pages/results/results.page';

export const routes: Routes = [
  {
    path: '',
    component: SearchPage,
  },
  {
    path: 'results',
    component: ResultsPage,
  },
];