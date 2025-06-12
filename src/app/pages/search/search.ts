import { Component } from '@angular/core';
import { SearchReferenceComponent } from '../../components/search/reference/reference';
import { Reference } from '../../models/reference';

@Component({
  selector: 'app-search',
  imports: [SearchReferenceComponent],
  templateUrl: './search.html',
  styleUrl: './search.scss',
})
export class SearchPage {
  onReferenceSubmit(data: Reference) {
    console.log('Reference submitted:', data);
  }
}
