import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SearchImagesComponent } from './images';

describe('Images', () => {
  let component: SearchImagesComponent;
  let fixture: ComponentFixture<SearchImagesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SearchImagesComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SearchImagesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
