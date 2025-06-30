import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProductMetricsComponent } from './metrics';

describe('Metrics', () => {
  let component: ProductMetricsComponent;
  let fixture: ComponentFixture<ProductMetricsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductMetricsComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductMetricsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
