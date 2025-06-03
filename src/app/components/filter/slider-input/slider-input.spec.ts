import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SliderInputComponent } from './slider-input.component';

describe('SliderInput', () => {
  let component: SliderInputComponent;
  let fixture: ComponentFixture<SliderInputComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SliderInputComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SliderInputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
