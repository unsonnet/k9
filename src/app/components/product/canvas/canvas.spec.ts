import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProductCanvasComponent } from './canvas';

describe('Canvas', () => {
  let component: ProductCanvasComponent;
  let fixture: ComponentFixture<ProductCanvasComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductCanvasComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductCanvasComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
