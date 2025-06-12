import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SearchReferenceComponent } from './reference';

describe('Reference', () => {
  let component: SearchReferenceComponent;
  let fixture: ComponentFixture<SearchReferenceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SearchReferenceComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SearchReferenceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
