import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ReactiveFormsModule,
  FormBuilder,
  Validators,
  FormGroup,
} from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { SearchImagesComponent } from '../images/images';

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
  form: FormGroup;
  materials = ['ceramic', 'porcelain'];
  countries = ['USA', 'Canada', 'UK', 'Germany', 'Mexico'];

  constructor(private fb: FormBuilder) {
    this.form = this.fb.group({
      material: ['', Validators.required],
      length: [null],
      width: [null],
      images: [[]],
    });
  }

  submit() {
    if (this.form.valid) {
      console.log('Form Submitted:', this.form.value);
    } else {
      this.form.markAllAsTouched();
    }
  }
}
