import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSliderModule } from '@angular/material/slider';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatButtonModule } from '@angular/material/button';
import {
  FilterGroups,
  shapeFilters,
  patternFilters,
  colorFilters,
} from '../../models/filters.model';
import { packageFilters } from '../../models/thresholds.model';
import { NumberInputComponent } from '../../components/filters/number-input/number-input.component';
import { SliderInputComponent } from '../../components/filters/slider-input/slider-input.component';

@Component({
  selector: 'app-filters',
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSliderModule,
    MatCheckboxModule,
    MatButtonModule,
    NumberInputComponent,
    SliderInputComponent,
  ],
  templateUrl: './filters.page.html',
  styleUrls: ['./filters.page.scss'],
})
export class FiltersPage {
  filterGroups: FilterGroups = new Map([
    [
      'shape',
      {
        label: 'Shape',
        filters: shapeFilters,
        includeMissing: false,
      },
    ],
    [
      'pattern',
      {
        label: 'Pattern',
        filters: patternFilters,
        includeMissing: false,
      },
    ],
    [
      'color',
      {
        label: 'Color',
        filters: colorFilters,
        includeMissing: false,
      },
    ],
  ]);

  applyFilters() {
    console.log('Applied filters:', packageFilters(this.filterGroups));
  }
}
