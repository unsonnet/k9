import { Component } from '@angular/core';
import { ResultsThresholdsComponent } from '../../components/results/thresholds/thresholds';
import { Thresholds } from '../../models/thresholds';

@Component({
  selector: 'app-results',
  imports: [ResultsThresholdsComponent],
  templateUrl: './results.html',
  styleUrl: './results.scss',
})
export class ResultsPage {
  handleApply(thresholds: Thresholds) {
    console.log('Thresholds received:', thresholds);
  }
}
