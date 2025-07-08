import { Routes } from '@angular/router';
import { SearchPage } from './pages/search/search';
import { ResultsPage } from './pages/results/results';
import { LoginPage } from './pages/login/login';

export const routes: Routes = [
  {
    path: '',
    component: LoginPage,
  },
  {
    path: 'search',
    component: SearchPage,
  },
  {
    path: 'results',
    component: ResultsPage,
  },
];
