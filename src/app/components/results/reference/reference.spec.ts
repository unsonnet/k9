import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ResultsReferenceComponent } from './reference';

describe('Reference', () => {
  let component: ResultsReferenceComponent;
  let fixture: ComponentFixture<ResultsReferenceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ResultsReferenceComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ResultsReferenceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
