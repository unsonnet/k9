import { Routes } from '@angular/router';
import { SearchPage } from './pages/search/search';
import { ResultsPage } from './pages/results/results';

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
