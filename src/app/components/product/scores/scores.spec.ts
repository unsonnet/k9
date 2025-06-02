import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProductScoresComponent } from './scores.component';

describe('ProductScores', () => {
  let component: ProductScoresComponent;
  let fixture: ComponentFixture<ProductScoresComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductScoresComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductScoresComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
