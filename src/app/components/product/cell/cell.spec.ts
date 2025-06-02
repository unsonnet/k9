import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ProductCellComponent } from './cell.component';

describe('ProductCell', () => {
  let component: ProductCellComponent;
  let fixture: ComponentFixture<ProductCellComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductCellComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductCellComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
