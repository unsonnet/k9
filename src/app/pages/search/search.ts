import { Component, signal } from '@angular/core';
import { Reference } from '../../models/reference';
import { SearchReferenceComponent } from '../../components/search/reference/reference';
import { SearchProgressComponent } from "../../components/search/progress/progress";

@Component({
  selector: 'app-search',
  imports: [SearchReferenceComponent, SearchProgressComponent],
  templateUrl: './search.html',
  styleUrl: './search.scss',
})
export class SearchPage {
  onReferenceSubmit(data: Reference) {
    console.log('Reference submitted:', data);
  }

  readonly loadingMessage = signal('Searching backed items...');
  readonly isErrored = signal(false);

  simulateProgress() {
    this.loadingMessage.set('Loading items...');
    this.isErrored.set(false);

    setTimeout(() => {
      this.loadingMessage.set('Something went wrong while fetching data.');
      this.isErrored.set(true);
    }, 3000);
  }
}
