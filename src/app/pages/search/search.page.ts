import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { QueryComponent } from '../../components/query/query/query.component';
import { Query } from '../../models/query.model';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, QueryComponent, MatProgressSpinnerModule],
  templateUrl: './search.page.html',
  styleUrls: ['./search.page.scss'],
})
export class SearchPageComponent {
  isLoading = false;
  statusText = 'Preparing search…';

  async startSearch(query: Query) {
    this.isLoading = true;
    this.statusText = 'Validating input…';
    await this.fakeStep('Calling similarity engine…');

    await this.fakeStep('Detecting patterns…');
    await this.fakeStep('Building result set…');
    this.statusText = 'Complete!';
    // Place your route change, data store update, etc. logic here.
  }

  private async fakeStep(next: string): Promise<void> {
    return new Promise((resolve) => {
      setTimeout(() => {
        this.statusText = next;
        resolve();
      }, 1000);
    });
  }
}
