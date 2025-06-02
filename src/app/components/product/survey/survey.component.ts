import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnChanges,
  SimpleChanges,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { SurveyResponse } from '../../../models/survey.model';

const defaultSurvey: SurveyResponse = {
  Color: 3,
  Pattern: 3,
  Shape: 3,
  Overall: 3,
};

@Component({
  selector: 'app-product-survey',
  standalone: true,
  imports: [CommonModule],
  templateUrl: `./survey.component.html`,
  styleUrl: './survey.component.scss',
})
export class ProductSurveyComponent implements OnChanges {
  @Input() value: SurveyResponse | null = null;
  @Output() valueChange = new EventEmitter<SurveyResponse>();

  responses: SurveyResponse = { ...defaultSurvey };

  // Automatically infer keys from defaultSurvey
  questionKeys = Object.keys(defaultSurvey) as Array<keyof SurveyResponse>;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['value']) {
      this.responses = this.value ? { ...this.value } : { ...defaultSurvey };
    }
  }

  onSelect(question: keyof SurveyResponse, score: number): void {
    this.responses = { ...this.responses, [question]: score };
    this.valueChange.emit(this.responses);
  }
}
