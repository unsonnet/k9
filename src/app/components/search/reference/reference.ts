import { Component, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ReactiveFormsModule,
  FormBuilder,
  Validators,
  FormGroup,
  FormControl,
} from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { SearchImagesComponent } from '../images/images';
import { Reference } from '../../../models/reference';

@Component({
  selector: 'app-search-reference',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    SearchImagesComponent,
  ],
  templateUrl: './reference.html',
  styleUrl: './reference.scss',
})
export class SearchReferenceComponent {
  readonly submitReference = output<Reference<File>>();

  materials = ['ceramic', 'porcelain'];
  referenceForm: FormGroup<{
    type: FormControl<string>;
    material: FormControl<string>;
    length: FormControl<number | null>;
    width: FormControl<number | null>;
    thickness: FormControl<number | null>;
    images: FormControl<File[]>;
  }>;

  constructor(private fb: FormBuilder) {
    this.referenceForm = new FormGroup({
      type: this.fb.nonNullable.control('tile'),
      material: this.fb.nonNullable.control('', {
        validators: Validators.required,
      }),
      length: this.fb.control<number | null>(null),
      width: this.fb.control<number | null>(null),
      thickness: this.fb.control<number | null>(null),
      images: this.fb.nonNullable.control([] as File[], {
        validators: Validators.required,
      }),
    });
  }

  onSubmit(): void {
    if (this.referenceForm.valid) {
      this.submitReference.emit(this.referenceForm.getRawValue());
    } else {
      this.referenceForm.markAllAsTouched();
    }
  }
}
