import { Component } from '@angular/core';
import { SearchReferenceComponent } from '../../components/search/reference/reference';

@Component({
  selector: 'app-search',
  imports: [SearchReferenceComponent],
  templateUrl: './search.html',
  styleUrl: './search.scss',
})
export class SearchPage {}
