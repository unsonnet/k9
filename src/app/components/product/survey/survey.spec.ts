import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProductSurveyComponent } from './survey.component';

describe('ProductSurvey', () => {
  let component: ProductSurveyComponent;
  let fixture: ComponentFixture<ProductSurveyComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductSurveyComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductSurveyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
