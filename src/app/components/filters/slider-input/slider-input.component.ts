import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatSliderModule } from '@angular/material/slider';

@Component({
  selector: 'app-slider-input',
  standalone: true,
  imports: [CommonModule, FormsModule, MatSliderModule],
  templateUrl: './slider-input.component.html',
  styleUrls: ['./slider-input.component.scss'],
})
export class SliderInputComponent {
  @Input() groupKey!: string;
  @Input() filterKey!: string;
  @Input() filterData!: { label: string; value: number };
}
