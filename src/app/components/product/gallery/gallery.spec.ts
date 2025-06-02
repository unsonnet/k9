import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProductGalleryComponent } from './gallery.component';

describe('ProductGallery', () => {
  let component: ProductGalleryComponent;
  let fixture: ComponentFixture<ProductGalleryComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductGalleryComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductGalleryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
