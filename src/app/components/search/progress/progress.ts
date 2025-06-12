import { Component, input } from '@angular/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-search-progress',
  standalone: true,
  imports: [MatProgressSpinnerModule],
  templateUrl: './progress.html',
  styleUrl: './progress.scss',
})
export class SearchProgressComponent {
  readonly message = input('');
  readonly isError = input(false);
}
