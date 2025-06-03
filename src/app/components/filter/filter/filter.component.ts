import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSliderModule } from '@angular/material/slider';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatButtonModule } from '@angular/material/button';
import { filterGroups } from '../../../models/filter.model';
import { packageFilters, Thresholds } from '../../../models/thresholds.model';
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

  @Output() thresholdsSubmit = new EventEmitter<Thresholds>();

  onFilter(): void {
    const thresholds = packageFilters(this.filterGroups);
    this.thresholdsSubmit.emit(thresholds);
  }
}
