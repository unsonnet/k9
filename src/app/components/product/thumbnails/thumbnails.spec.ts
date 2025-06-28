import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProductThumbnailsComponent } from './thumbnails';

describe('Thumbnails', () => {
  let component: ProductThumbnailsComponent;
  let fixture: ComponentFixture<ProductThumbnailsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProductThumbnailsComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductThumbnailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
