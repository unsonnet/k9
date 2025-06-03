import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSliderModule } from '@angular/material/slider';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatButtonModule } from '@angular/material/button';
import { filterGroups } from '../../../models/filter.model';
import { packageFilters } from '../../../models/thresholds.model';
import { NumberInputComponent } from '../number-input/number-input.component';
import { SliderInputComponent } from '../slider-input/slider-input.component';

@Component({
  selector: 'app-filter',
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
  templateUrl: './filter.component.html',
  styleUrls: ['./filter.component.scss'],
})
export class FilterComponent {
  filterGroups = filterGroups;

  applyFilters() {
    console.log('Applied filters:', packageFilters(this.filterGroups));
  }
}
