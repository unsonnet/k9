import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-search-progress',
  standalone: true,
  imports: [CommonModule, MatProgressSpinnerModule],
  templateUrl: './progress.html',
  styleUrl: './progress.scss',
})
export class SearchProgressComponent {
  readonly loadingMessage = input.required<string>();
  readonly errorMessage = input.required<string>();
}
